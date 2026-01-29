from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import os
import tempfile
import traceback
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from your_cleaning_script import NoonCleaner, AmazonCleaner, RevibeCleaner, TalabatCleaner, CareemCleaner

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
app.config['PRODUCT_CSV'] = 'product.csv'
app.config['COMMENTS_JSON'] = 'comments.json'

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_cleaner_class(marketplace):
    cleaners = {
        'Noon': NoonCleaner,
        'Amazon': AmazonCleaner,
        'Revibe': RevibeCleaner,
        'Talabat': TalabatCleaner,
        'Careem': CareemCleaner
    }
    return cleaners.get(marketplace)

def load_comments():
    """Load comments from JSON file"""
    try:
        if os.path.exists(app.config['COMMENTS_JSON']):
            with open(app.config['COMMENTS_JSON'], 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {"comments": []}

def save_comments(data):
    """Save comments to JSON file"""
    try:
        with open(app.config['COMMENTS_JSON'], 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except:
        return False

# ============ ROUTES ============

@app.route('/')
def home():
    comments_data = load_comments()
    # Sort comments by timestamp (newest first)
    comments_data["comments"].sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return render_template('index.html', comments=comments_data["comments"])

@app.route('/cleaning')
def cleaning():
    return render_template('cleaning.html')

@app.route('/add-data')
def add_data():
    # Read product data for filters
    try:
        if os.path.exists(app.config['PRODUCT_CSV']):
            df = pd.read_csv(app.config['PRODUCT_CSV'])
            product_count = len(df)
            
            # Get unique values for filters
            brands = sorted(df['Brand'].dropna().unique().tolist()) if 'Brand' in df.columns else []
            categories = sorted(df['Category'].dropna().unique().tolist()) if 'Category' in df.columns else []
            sub_categories = sorted(df['Sub-Category'].dropna().unique().tolist()) if 'Sub-Category' in df.columns else []
            skus = sorted(df['SKU'].dropna().unique().tolist()) if 'SKU' in df.columns else []
            
        else:
            product_count = 0
            brands = categories = sub_categories = skus = []
            
        return render_template('add_data.html', 
                             product_count=product_count,
                             brands=brands,
                             categories=categories,
                             sub_categories=sub_categories,
                             skus=skus)
                             
    except Exception as e:
        print(f"Error in add-data route: {e}")
        return render_template('add_data.html', 
                             product_count=0,
                             brands=[],
                             categories=[],
                             sub_categories=[],
                             skus=[])

# ============ API ENDPOINTS ============

# Store cleaned data in memory
cleaned_data_store = {}

# ================================================ Comments API ===========================================

# Comments API with replies
@app.route('/api/comments', methods=['GET'])
def get_comments():
    """Get all comments with replies"""
    try:
        comments_data = load_comments()
        
        # Sort comments by timestamp (newest first)
        comments_data["comments"].sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return jsonify({
            'success': True,
            'comments': comments_data.get("comments", [])
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/comments/add', methods=['POST'])
def add_comment():
    """Add a new comment or reply"""
    try:
        data = request.json
        name = data.get('name', '').strip()
        comment = data.get('comment', '').strip()
        parent_id = data.get('parent_id')  # None for top-level comment, ID for reply
        
        if not name or not comment:
            return jsonify({'error': 'Name and comment are required'}), 400
        
        comments_data = load_comments()
        
        # Generate unique ID
        import uuid
        comment_id = str(uuid.uuid4())[:8]
        
        new_comment = {
            'id': comment_id,
            'parent_id': parent_id,
            'name': name,
            'comment': comment,
            'timestamp': datetime.now().isoformat(),
            'date': datetime.now().strftime('%d %b %Y'),
            'time': datetime.now().strftime('%I:%M %p'),
            'replies': []  # Initialize empty replies array
        }
        
        if not parent_id:
            # Top-level comment
            comments_data["comments"].insert(0, new_comment)
        else:
            # Find parent comment and add reply
            def find_and_add_reply(comments, parent_id, reply):
                for comment in comments:
                    if comment['id'] == parent_id:
                        if 'replies' not in comment:
                            comment['replies'] = []
                        comment['replies'].insert(0, reply)
                        return True
                    elif 'replies' in comment and comment['replies']:
                        if find_and_add_reply(comment['replies'], parent_id, reply):
                            return True
                return False
            
            if not find_and_add_reply(comments_data["comments"], parent_id, new_comment):
                return jsonify({'error': 'Parent comment not found'}), 404
        
        if save_comments(comments_data):
            return jsonify({
                'success': True,
                'message': 'Comment added successfully',
                'comment': new_comment
            })
        else:
            return jsonify({'error': 'Failed to save comment'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/comments/delete/<comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    """Delete a comment or reply"""
    try:
        comments_data = load_comments()
        
        def delete_comment_recursive(comments, comment_id):
            for i, comment in enumerate(comments):
                if comment['id'] == comment_id:
                    # Check if it has replies
                    if 'replies' in comment and comment['replies']:
                        # Mark as deleted instead of removing
                        comment['deleted'] = True
                        comment['name'] = '[Deleted]'
                        comment['comment'] = 'This comment has been deleted'
                    else:
                        # Remove if no replies
                        del comments[i]
                    return True
                elif 'replies' in comment and comment['replies']:
                    if delete_comment_recursive(comment['replies'], comment_id):
                        return True
            return False
        
        if delete_comment_recursive(comments_data["comments"], comment_id):
            if save_comments(comments_data):
                return jsonify({'success': True, 'message': 'Comment deleted successfully'})
            else:
                return jsonify({'error': 'Failed to save changes'}), 500
        else:
            return jsonify({'error': 'Comment not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
# Cleaning API
@app.route('/api/clean', methods=['POST'])
def clean_data():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        marketplace = request.form.get('marketplace')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not marketplace:
            return jsonify({'error': 'No marketplace selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Allowed: csv, xlsx, xls'}), 400
        
        # Save uploaded file temporarily
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        temp_input = tempfile.NamedTemporaryFile(delete=False, suffix='.' + file_ext)
        file.save(temp_input.name)
        temp_input.close()
        
        # Create cleaner instance
        cleaner_class = get_cleaner_class(marketplace)
        if not cleaner_class:
            return jsonify({'error': f'Cleaner for {marketplace} not found'}), 400
        
        try:
            # Process the file
            cleaner = cleaner_class(temp_input.name)
            cleaner.clean()
            
            # Get all data
            all_data = cleaner.data.to_dict('records')
            columns = cleaner.data.columns.tolist()
            
            # Clean up temp file
            os.unlink(temp_input.name)
            
            # Generate unique ID for this cleaning session
            import uuid
            session_id = str(uuid.uuid4())
            
            # Store in memory
            cleaned_data_store[session_id] = {
                'data': all_data,
                'columns': columns,
                'marketplace': marketplace,
                'timestamp': datetime.now().isoformat()
            }
            
            return jsonify({
                'success': True,
                'preview': all_data[:50],  # First 50 rows for preview
                'all_data': all_data,      # All rows for download
                'columns': columns,
                'rows_count': len(all_data),
                'session_id': session_id,
                'filename': f"Cleaned_{marketplace}_Data.csv"
            })
            
        except Exception as e:
            # Clean up temp file on error
            if os.path.exists(temp_input.name):
                os.unlink(temp_input.name)
            raise e
        
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error: {e}\nTrace: {error_trace}")
        return jsonify({'error': str(e), 'trace': error_trace}), 500

@app.route('/api/download/<session_id>', methods=['GET'])
def download_cleaned(session_id):
    try:
        if session_id not in cleaned_data_store:
            return jsonify({'error': 'Session expired or invalid'}), 404
        
        data = cleaned_data_store[session_id]
        marketplace = data['marketplace']
        
        # Create DataFrame from stored data
        df = pd.DataFrame(data['data'])
        
        # Create CSV in memory
        from io import StringIO
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        
        # Create response
        from io import BytesIO
        mem = BytesIO()
        mem.write(csv_buffer.getvalue().encode('utf-8'))
        mem.seek(0)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"Cleaned_{marketplace}_{timestamp}.csv"
        
        return send_file(
            mem,
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Products API with filtering
@app.route('/api/products', methods=['GET'])
def get_products():
    try:
        if not os.path.exists(app.config['PRODUCT_CSV']):
            return jsonify({
                'success': True,
                'products': [],
                'columns': ['Brand', 'Category', 'Sub-Category', 'Product Titles', 'SKU', 'Partner SKU'],
                'total': 0,
                'filters': {
                    'brands': [],
                    'categories': [],
                    'sub_categories': [],
                    'skus': []
                }
            })
        
        df = pd.read_csv(app.config['PRODUCT_CSV'])
        
        # Get filter parameters
        brand_filter = request.args.get('brand', '')
        category_filter = request.args.get('category', '')
        sub_category_filter = request.args.get('sub_category', '')
        sku_filter = request.args.get('sku', '')
        search_query = request.args.get('search', '')
        
        # Apply filters
        filtered_df = df.copy()
        
        if brand_filter:
            filtered_df = filtered_df[filtered_df['Brand'].astype(str).str.contains(brand_filter, case=False, na=False)]
        
        if category_filter:
            filtered_df = filtered_df[filtered_df['Category'].astype(str).str.contains(category_filter, case=False, na=False)]
        
        if sub_category_filter:
            filtered_df = filtered_df[filtered_df['Sub-Category'].astype(str).str.contains(sub_category_filter, case=False, na=False)]
        
        if sku_filter:
            filtered_df = filtered_df[filtered_df['SKU'].astype(str).str.contains(sku_filter, case=False, na=False)]
        
        if search_query:
            search_terms = search_query.lower().split()
            mask = pd.Series([False] * len(filtered_df))
            for term in search_terms:
                mask = mask | (
                    filtered_df['Brand'].astype(str).str.lower().str.contains(term, na=False) |
                    filtered_df['Category'].astype(str).str.lower().str.contains(term, na=False) |
                    filtered_df['Sub-Category'].astype(str).str.lower().str.contains(term, na=False) |
                    filtered_df['Product Titles'].astype(str).str.lower().str.contains(term, na=False) |
                    filtered_df['SKU'].astype(str).str.lower().str.contains(term, na=False) |
                    filtered_df['Partner SKU'].astype(str).str.lower().str.contains(term, na=False)
                )
            filtered_df = filtered_df[mask]
        
        # Get random 50 products or all if less than 50
        if len(filtered_df) > 50:
            filtered_df = filtered_df.sample(n=50, random_state=42)
        
        products = filtered_df.to_dict('records')
        columns = df.columns.tolist()
        
        # Get unique values for filters from FULL dataset
        brands = sorted(df['Brand'].dropna().unique().tolist()) if 'Brand' in df.columns else []
        categories = sorted(df['Category'].dropna().unique().tolist()) if 'Category' in df.columns else []
        sub_categories = sorted(df['Sub-Category'].dropna().unique().tolist()) if 'Sub-Category' in df.columns else []
        skus = sorted(df['SKU'].dropna().unique().tolist()) if 'SKU' in df.columns else []
        
        return jsonify({
            'success': True,
            'products': products,
            'columns': columns,
            'total': len(df),
            'filtered_total': len(filtered_df),
            'filters': {
                'brands': brands,
                'categories': categories,
                'sub_categories': sub_categories,
                'skus': skus
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/add', methods=['POST'])
def add_product():
    try:
        data = request.json
        required_fields = ['Brand', 'Category', 'Sub-Category', 'Product Titles', 'SKU', 'Partner SKU']
        
        # Validate required fields
        for field in required_fields:
            if field not in data or not str(data[field]).strip():
                return jsonify({'error': f'Missing or empty field: {field}'}), 400
        
        # Read existing data or create new
        if os.path.exists(app.config['PRODUCT_CSV']):
            df = pd.read_csv(app.config['PRODUCT_CSV'])
        else:
            df = pd.DataFrame(columns=required_fields)
        
        # Check for duplicate SKU
        if data['SKU'] in df['SKU'].astype(str).values:
            return jsonify({'error': f"SKU '{data['SKU']}' already exists"}), 400
        
        # Add new row
        new_row = pd.DataFrame([data])
        df = pd.concat([df, new_row], ignore_index=True)
        
        # Save back to CSV
        df.to_csv(app.config['PRODUCT_CSV'], index=False)
        
        # Get updated filter values
        brands = sorted(df['Brand'].dropna().unique().tolist()) if 'Brand' in df.columns else []
        categories = sorted(df['Category'].dropna().unique().tolist()) if 'Category' in df.columns else []
        sub_categories = sorted(df['Sub-Category'].dropna().unique().tolist()) if 'Sub-Category' in df.columns else []
        skus = sorted(df['SKU'].dropna().unique().tolist()) if 'SKU' in df.columns else []
        
        return jsonify({
            'success': True,
            'message': 'Product added successfully',
            'total': len(df),
            'filters': {
                'brands': brands,
                'categories': categories,
                'sub_categories': sub_categories,
                'skus': skus
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/bulk', methods=['POST'])
def bulk_add_products():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.csv'):
            return jsonify({'error': 'Only CSV files allowed for bulk upload'}), 400
        
        # Read uploaded CSV
        bulk_df = pd.read_csv(file)
        
        # Check required columns
        required_columns = ['Brand', 'Category', 'Sub-Category', 'Product Titles', 'SKU', 'Partner SKU']
        missing_columns = [col for col in required_columns if col not in bulk_df.columns]
        
        if missing_columns:
            return jsonify({'error': f'Missing columns: {", ".join(missing_columns)}'}), 400
        
        # Read existing data or create new
        if os.path.exists(app.config['PRODUCT_CSV']):
            existing_df = pd.read_csv(app.config['PRODUCT_CSV'])
        else:
            existing_df = pd.DataFrame(columns=required_columns)
        
        # Find new SKUs
        existing_skus = set(existing_df['SKU'].astype(str).str.strip())
        new_skus = set(bulk_df['SKU'].astype(str).str.strip())
        
        # Filter out duplicates
        unique_skus = new_skus - existing_skus
        new_products_df = bulk_df[bulk_df['SKU'].astype(str).str.strip().isin(unique_skus)]
        
        if len(new_products_df) == 0:
            return jsonify({'error': 'All SKUs already exist in database'}), 400
        
        # Merge data
        combined_df = pd.concat([existing_df, new_products_df], ignore_index=True)
        
        # Save back to CSV
        combined_df.to_csv(app.config['PRODUCT_CSV'], index=False)
        
        # Get updated filter values
        brands = sorted(combined_df['Brand'].dropna().unique().tolist()) if 'Brand' in combined_df.columns else []
        categories = sorted(combined_df['Category'].dropna().unique().tolist()) if 'Category' in combined_df.columns else []
        sub_categories = sorted(combined_df['Sub-Category'].dropna().unique().tolist()) if 'Sub-Category' in combined_df.columns else []
        skus = sorted(combined_df['SKU'].dropna().unique().tolist()) if 'SKU' in combined_df.columns else []
        
        return jsonify({
            'success': True,
            'message': f'Added {len(new_products_df)} new products',
            'added': len(new_products_df),
            'skipped': len(bulk_df) - len(new_products_df),
            'total': len(combined_df),
            'filters': {
                'brands': brands,
                'categories': categories,
                'sub_categories': sub_categories,
                'skus': skus
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/template/product', methods=['GET'])
def download_product_template():
    """Download product template CSV"""
    try:
        # Create template CSV
        template_data = {
            'Brand': ['ExampleBrand', 'AnotherBrand'],
            'Category': ['Electronics', 'Home & Kitchen'],
            'Sub-Category': ['Laptops', 'Cookware'],
            'Product Titles': ['Sample Laptop 15-inch', 'Sample Cookware Set'],
            'SKU': ['EX001', 'EX002'],
            'Partner SKU': ['PSKU_EX001', 'PSKU_EX002']
        }
        
        df = pd.DataFrame(template_data)
        
        # Create CSV in memory
        from io import StringIO
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        
        # Create response
        from io import BytesIO
        mem = BytesIO()
        mem.write(csv_buffer.getvalue().encode('utf-8'))
        mem.seek(0)
        
        return send_file(
            mem,
            as_attachment=True,
            download_name='product_template.csv',
            mimetype='text/csv'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sample-data/<marketplace>', methods=['GET'])
def get_sample_data(marketplace):
    """Generate sample data for testing"""
    try:
        import pandas as pd
        import numpy as np
        from datetime import datetime, timedelta
        
        # Generate sample data based on marketplace
        if marketplace == 'Noon':
            data = {
                'order_timestamp': [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d %H:%M:%S') for i in range(20)],
                'item_nr': [f'NOON{i:06d}' for i in range(100, 120)],
                'sku': ['ZE76429E45999B752B788Z-1', 'Z7C540D2EC016330A32A6Z-1', 'Z510404DC1F6F97610CD9Z-1'] * 7,
                'status': ['Shipped', 'Delivered', 'CIR'] * 7,
                'id_partner': ['46272', '181587', '47461'] * 7,
                'country_code': ['SA', 'AE', 'SA'] * 7,
                'partner_sku': ['WHGS30', 'P1CLB5', 'RWS250'] * 7,
                'fulfillment_model': ['Fulfilled by Noon (FBN)', 'Fulfilled by Partner (FBP)'] * 10,
                'offer_price': [99.99, 49.99, 29.99] * 7
            }
            df = pd.DataFrame(data)
            
        elif marketplace == 'Amazon':
            data = {
                'purchase-date': [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d %H:%M:%S') for i in range(20)],
                'amazon-order-id': [f'AMZ{i:06d}' for i in range(200, 220)],
                'sku': ['ZE76429E45999B752B788Z-1', 'Z7C540D2EC016330A32A6Z-1', 'Z510404DC1F6F97610CD9Z-1'] * 7,
                'item-status': ['Shipped', 'Pending', 'Cancelled'] * 7,
                'ship-country': ['SA', 'AE', 'BH'] * 7,
                'sales-channel': ['Amazon.ae', 'Amazon.sa'] * 10,
                'product-name': ['Product A', 'Product B', 'Product C'] * 7,
                'asin': ['B0ABCD1234', 'B0EFGH5678', 'B0IJKL9012'] * 7,
                'fulfillment-channel': ['Amazon', 'Merchant'] * 10,
                'item-price': [89.99, 45.99, 25.99] * 7,
                'quantity': [1, 2, 1] * 7
            }
            df = pd.DataFrame(data)
            
        else:
            return jsonify({'error': f'Sample data not available for {marketplace}'}), 404
        
        # Create CSV in memory
        from io import StringIO, BytesIO
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        
        mem = BytesIO()
        mem.write(csv_buffer.getvalue().encode('utf-8'))
        mem.seek(0)
        
        return send_file(
            mem,
            as_attachment=True,
            download_name=f"Sample_{marketplace}_Data.csv",
            mimetype='text/csv',
            cache_timeout=0
        )
        
    except Exception as e:
        print(f"Error generating sample data: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Ensure product.csv exists
    if not os.path.exists('product.csv'):
        # Create with headers
        df = pd.DataFrame(columns=['Brand', 'Category', 'Sub-Category', 'Product Titles', 'SKU', 'Partner SKU'])
        df.to_csv('product.csv', index=False)
        print("Created product.csv with headers")
    
    # Ensure comments.json exists
    if not os.path.exists('comments.json'):
        with open('comments.json', 'w', encoding='utf-8') as f:
            json.dump({"comments": []}, f, indent=2)
        print("Created comments.json")
    
    app.run(debug=True, port=5000)