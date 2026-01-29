import pandas as pd
import numpy as np
from dateutil import parser
import os

class BaseCleaner:
    def __init__(self, file_path):
        """
        Initialize with file path
        """
        self.file_path = file_path
        self.data = None
        self.master_df = None
        self.load_master_data()

    def load_master_data(self):
        """Load master product data"""
        try:
            if os.path.exists('product.csv'):
                self.master_df = pd.read_csv('product.csv')
                # Clean SKU columns
                if 'SKU' in self.master_df.columns:
                    self.master_df['SKU'] = self.master_df['SKU'].astype(str).str.strip()
                if 'Partner SKU' in self.master_df.columns:
                    self.master_df['Partner SKU'] = self.master_df['Partner SKU'].astype(str).str.strip()
        except Exception as e:
            print(f"Warning: Could not load master data: {e}")
            self.master_df = pd.DataFrame()

    def read_data(self):
        try:
            if self.file_path.endswith('.csv'):
                self.data = pd.read_csv(self.file_path, dtype=str)
            elif self.file_path.endswith(('.xlsx', '.xls')):
                self.data = pd.read_excel(self.file_path, engine='openpyxl', dtype=str)
            print(f"Data Loaded: {self.data.shape}")
        except Exception as e:
            print(f"Error Reading File: {e}")
            raise e

    def save_data(self, output_file):
        try:
            self.data.to_csv(output_file, index=False)
            print(f"Data Saved to {output_file}")
        except Exception as e:
            print(f"Error Saving File: {e}")

    def convert_date(self, column_name):
        try:
            self.data[column_name] = pd.to_datetime(self.data[column_name], errors='coerce')
        except Exception as e:
            print(f"Error Converting Date: {e}")

    def convert_date1(self, column_name):
        try:
            # Handle mixed date formats
            self.data[column_name] = self.data[column_name].apply(
                lambda x: parser.parse(str(x), dayfirst=True, fuzzy=True) if pd.notnull(x) and str(x).strip() else pd.NaT
            )
        except Exception as e:
            print(f"Error Converting Date: {e}")

# Noon cleaner - FIXED column order
class NoonCleaner(BaseCleaner):
    def clean(self):
        try:
            self.read_data()
            
            # Convert all columns to string first
            self.data = self.data.astype(str)
            
            # Check if required columns exist
            required_columns = ['order_timestamp', 'item_nr', 'sku', 'status', 'id_partner', 
                              'country_code', 'partner_sku', 'fulfillment_model', 'offer_price']
            
            # Find which columns actually exist
            existing_columns = [col for col in required_columns if col in self.data.columns]
            missing_columns = [col for col in required_columns if col not in self.data.columns]
            
            if missing_columns:
                print(f"Warning: Missing columns in Noon data: {missing_columns}")
                print(f"Available columns: {list(self.data.columns)}")
            
            # Keep only existing required columns
            self.data = self.data[existing_columns]

            # Rename columns
            rename_map = {
                'order_timestamp': 'Date',
                'item_nr': 'Order Number',
                'sku': 'SKU',
                'status': 'Status',
                'id_partner': 'Partner Id',
                'country_code': 'Country',
                'partner_sku': 'Partner SKU',
                'fulfillment_model': 'Fullfilment',
                'offer_price': 'Sales_Price'
            }
            
            # Apply rename only for existing columns
            actual_rename = {k: v for k, v in rename_map.items() if k in self.data.columns}
            self.data = self.data.rename(columns=actual_rename)

            # Column 0 ------> Date
            if 'Date' in self.data.columns:
                self.convert_date('Date')

            # Column 1 ------> Month
            if 'Date' in self.data.columns:
                self.data.insert(1, 'Month', self.data['Date'].dt.strftime('%B'))
            else:
                self.data.insert(1, 'Month', '')

            # Column 2 ------> Month Number

            if 'Date' in self.data.columns:
                self.data.insert(2, 'Month Number', self.data['Date'].dt.month.astype('Int64'))
            else:
                self.data.insert(2, 'Month Number', '')

            # Column 3 ------> Year
            if 'Date' in self.data.columns:
                self.data.insert(3, 'Year', self.data['Date'].dt.year.astype('Int64'))
            else:
                self.data.insert(3, 'Year', '')

            # Column 8 ------> Nub Partner
            if 'Partner Id' in self.data.columns:
                self.data.insert(8, 'Nub Partner', self.data['Partner Id'].apply(self.get_nub_partner))
            else:
                self.data.insert(8, 'Nub Partner', '')

            # ✅ FIX: Brand, Category, Sub-Category को सही position में insert करें
            # Current columns after insertions: 
            # 0: Date, 1: Month, 2: Month Number, 3: Year, 4: Order Number, 
            # 5: SKU, 6: Status, 7: Partner Id, 8: Nub Partner, 9: Country
            
            # Column 10 -----> Brand Name (Partner Id के बाद)
            self.data.insert(10, 'Brand Name', "")
            
            # Column 11 -----> Category
            self.data.insert(11, 'Category', "")
            
            # Column 12 -----> Sub-Category
            self.data.insert(12, 'Sub-Category', "")
            
            # Column 13 -----> Channel
            self.data.insert(13, 'Channel', 'Noon')
            
            # Column 14 -----> Channel Item Name
            self.data.insert(14, 'Channel Item Name', "")
            
            # Add remaining columns if they exist
            col_index = 15
            if 'Partner SKU' in self.data.columns:
                # Move to correct position if needed
                if 'Partner SKU' not in [self.data.columns[col_index]]:
                    partner_sku_col = self.data.pop('Partner SKU')
                    self.data.insert(col_index, 'Partner SKU', partner_sku_col)
                col_index += 1
            
            if 'Fullfilment' in self.data.columns:
                if 'Fullfilment' not in [self.data.columns[col_index]]:
                    fulfillment_col = self.data.pop('Fullfilment')
                    self.data.insert(col_index, 'Fullfilment', fulfillment_col)
                col_index += 1
            
            if 'Sales_Price' in self.data.columns:
                if 'Sales_Price' not in [self.data.columns[col_index]]:
                    price_col = self.data.pop('Sales_Price')
                    self.data.insert(col_index, 'Sales_Price', price_col)
                col_index += 1
            
            # Add QTY and GMV at the end
            self.data['QTY'] = 1
            
            if 'Sales_Price' in self.data.columns:
                try:
                    self.data['Sales_Price'] = pd.to_numeric(self.data['Sales_Price'], errors='coerce').fillna(0)
                    self.data['GMV'] = self.data['Sales_Price'] * self.data['QTY']
                except:
                    self.data['GMV'] = 0
            else:
                self.data['GMV'] = 0

            # Filter irrelevant statuses if column exists
            if 'Status' in self.data.columns:
                irrelevant_statuses = ['Unshipped', 'Pending','Undelivered','Confirmed','Created','Exported','Fulfilling','Could Not Be Delivered','Processing']
                self.data = self.data[~self.data['Status'].isin(irrelevant_statuses)]

            # Replace values if columns exist
            if 'Country' in self.data.columns:
                self.data['Country'] = self.data['Country'].replace({'SA':'Saudi', 'AE':'UAE'})
            
            if 'Status' in self.data.columns:
                self.data['Status'] = self.data['Status'].replace({'Shipped':'Delivered','CIR':'Cancelled'})
            
            if 'Fullfilment' in self.data.columns:
                self.data['Fullfilment'] = self.data['Fullfilment'].replace({
                    'Fulfilled by Noon (FBN)':'FBN', 'Fulfilled by Partner (FBP)':'FBP'})

            # Fill blanks from master CSV if available
            if not self.master_df.empty and 'SKU' in self.data.columns:
                # Clean SKU
                self.data['SKU'] = self.data['SKU'].astype(str).str.strip()
                
                # Convert blanks to NaN
                cols_to_fill = ['Brand Name', 'Category', 'Sub-Category', 'Channel Item Name']
                for col in cols_to_fill:
                    if col in self.data.columns:
                        self.data[col] = self.data[col].replace(r'^\s*$', np.nan, regex=True)
                
                # Merge with master data
                if 'SKU' in self.master_df.columns:
                    master_subset = self.master_df[['SKU', 'Brand', 'Category', 'Sub-Category', 'Product Titles']].copy()
                    master_subset.columns = ['SKU', 'Brand_master', 'Category_master', 'Sub-Category_master', 'Product_Titles_master']
                    
                    self.data = self.data.merge(
                        master_subset,
                        on='SKU',
                        how='left'
                    )
                    
                    # Fill empty values from master
                    if 'Brand Name' in self.data.columns and 'Brand_master' in self.data.columns:
                        self.data['Brand Name'] = self.data['Brand Name'].fillna(self.data['Brand_master'])
                    
                    if 'Category' in self.data.columns and 'Category_master' in self.data.columns:
                        self.data['Category'] = self.data['Category'].fillna(self.data['Category_master'])
                    
                    if 'Sub-Category' in self.data.columns and 'Sub-Category_master' in self.data.columns:
                        self.data['Sub-Category'] = self.data['Sub-Category'].fillna(self.data['Sub-Category_master'])
                    
                    if 'Channel Item Name' in self.data.columns and 'Product_Titles_master' in self.data.columns:
                        self.data['Channel Item Name'] = self.data['Channel Item Name'].fillna(self.data['Product_Titles_master'])
                    
                    # Drop helper columns
                    columns_to_drop = ['Brand_master', 'Category_master', 'Sub-Category_master', 'Product_Titles_master']
                    for col in columns_to_drop:
                        if col in self.data.columns:
                            self.data = self.data.drop(columns=[col])

            # Set GMV = 0 for cancelled orders
            if 'Status' in self.data.columns and 'GMV' in self.data.columns:
                self.data.loc[self.data['Status'].str.strip().str.upper() == 'CANCELLED', 'GMV'] = 0

            # Fill NaN values with empty string
            self.data = self.data.fillna('')
            
            # Ensure correct column order
            expected_columns = ['Date', 'Month', 'Month Number', 'Year', 'Order Number', 'SKU', 
                              'Status', 'Partner Id', 'Nub Partner', 'Country', 'Brand Name',
                              'Category', 'Sub-Category', 'Channel', 'Channel Item Name',
                              'Partner SKU', 'Fullfilment', 'Sales_Price', 'QTY', 'GMV']
            
            # Add any missing columns
            for col in expected_columns:
                if col not in self.data.columns:
                    self.data[col] = ''
            
            # Reorder columns
            self.data = self.data[expected_columns]
            
            print(f"Noon Cleaned Data Shape: {self.data.shape}")
            print(f"Noon Columns: {list(self.data.columns)}")

        except Exception as e:
            print(f"Error Cleaning Noon Data: {e}")
            import traceback
            traceback.print_exc()
            raise e

    def get_nub_partner(self, pid):
        pid_str = str(pid).strip()
        if pid_str in ['46272', '46272']:
            return 'Nub-Partner 46272'
        elif pid_str in ['181587', '181587']:
            return 'Nub-Partner 181587'
        elif pid_str in ['47461', '47461']:
            return 'Nub-Partner 47461'
        elif pid_str in ['74949', '74949']:
            return 'Nub-Partner 74949'
        else:
            return 'Null'

# Amazon Cleaner - FIXED error handling
class AmazonCleaner(BaseCleaner):
    def __init__(self, file_path):
        super().__init__(file_path)

    def read_data(self):
        try:
            if self.file_path.endswith('.csv'):
                # CSV file - read as string to avoid type issues
                self.data = pd.read_csv(self.file_path, dtype=str)
                # Try to detect if Partner ID column exists
                if 'Partner ID' not in self.data.columns and 'Partner' in self.data.columns:
                    self.data = self.data.rename(columns={'Partner': 'Partner ID'})
                elif 'Partner ID' not in self.data.columns and 'partner_id' in self.data.columns:
                    self.data = self.data.rename(columns={'partner_id': 'Partner ID'})
                elif 'Partner ID' not in self.data.columns:
                    self.data['Partner ID'] = 'Amazon'
                    
            elif self.file_path.endswith(('.xlsx', '.xls')):
                # Excel file - handle multiple sheets
                try:
                    xls = pd.ExcelFile(self.file_path, engine='openpyxl')
                    available_sheets = xls.sheet_names
                    
                    if len(available_sheets) > 1:
                        # Multiple sheet case
                        all_dfs = []
                        for sheet in available_sheets:
                            try:
                                df = pd.read_excel(self.file_path, sheet_name=sheet, engine='openpyxl', dtype=str)
                                df['Partner ID'] = sheet
                                # Remove duplicate header rows if any
                                if len(df) > 0 and df.iloc[0, 0] == df.columns[0]:
                                    df = df.iloc[1:].reset_index(drop=True)
                                all_dfs.append(df)
                            except Exception as sheet_error:
                                print(f"Warning: Error reading sheet {sheet}: {sheet_error}")
                                continue
                        
                        if all_dfs:
                            self.data = pd.concat(all_dfs, ignore_index=True)
                        else:
                            raise Exception("No valid sheets found in Excel file")
                    else:
                        # Single sheet case
                        sheet = available_sheets[0]
                        self.data = pd.read_excel(self.file_path, sheet_name=sheet, engine='openpyxl', dtype=str)
                        self.data['Partner ID'] = sheet
                        # Remove duplicate header rows
                        if len(self.data) > 0 and self.data.iloc[0, 0] == self.data.columns[0]:
                            self.data = self.data.iloc[1:].reset_index(drop=True)
                            
                except Exception as excel_error:
                    print(f"Excel read error: {excel_error}")
                    # Try as CSV if Excel fails
                    self.data = pd.read_csv(self.file_path, dtype=str)
                    self.data['Partner ID'] = 'Amazon'

            print(f"Amazon Data Loaded: {self.data.shape}")
            print(f"Amazon Columns: {list(self.data.columns)}")

        except Exception as e:
            print(f"Error Reading Amazon File: {e}")
            import traceback
            traceback.print_exc()
            raise e

    def clean(self):
        try:
            self.read_data()
            
            # Convert all to string first
            self.data = self.data.astype(str)
            
            # Define required Amazon columns (with variations)
            amazon_columns_variations = {
                'purchase-date': ['purchase-date', 'purchase_date', 'purchasedate', 'Purchase Date'],
                'amazon-order-id': ['amazon-order-id', 'amazon_order_id', 'amazonorderid', 'Amazon Order ID'],
                'sku': ['sku', 'SKU', 'seller-sku', 'seller_sku'],
                'item-status': ['item-status', 'item_status', 'itemstatus', 'Item Status'],
                'ship-country': ['ship-country', 'ship_country', 'shipcountry', 'Ship Country'],
                'sales-channel': ['sales-channel', 'sales_channel', 'saleschannel', 'Sales Channel'],
                'product-name': ['product-name', 'product_name', 'productname', 'Product Name'],
                'asin': ['asin', 'ASIN'],
                'fulfillment-channel': ['fulfillment-channel', 'fulfillment_channel', 'fulfillmentchannel', 'Fulfillment Channel'],
                'item-price': ['item-price', 'item_price', 'itemprice', 'Item Price'],
                'quantity': ['quantity', 'Quantity']
            }
            
            # Map variations to standard names
            column_mapping = {}
            for standard_name, variations in amazon_columns_variations.items():
                for var in variations:
                    if var in self.data.columns:
                        column_mapping[var] = standard_name
                        break
            
            # Rename columns to standard names
            self.data = self.data.rename(columns=column_mapping)
            
            # Check which standard columns we have
            standard_columns = list(amazon_columns_variations.keys()) + ['Partner ID']
            existing_columns = [col for col in standard_columns if col in self.data.columns]
            
            print(f"Existing Amazon columns after mapping: {existing_columns}")
            
            # Keep only existing columns
            self.data = self.data[existing_columns]
            
            # Rename to final column names
            rename_map = {
                'purchase-date': 'Date',
                'amazon-order-id': 'Order Number',
                'sku': 'SKU',
                'item-status': 'Status',
                'ship-country': 'Country',
                'sales-channel': 'Channel',
                'product-name': 'Channel Item Name',
                'asin': 'Partner SKU',
                'fulfillment-channel': 'Fulfillment',
                'item-price': 'Sales price',
                'quantity': 'QTY'
            }
            
            # Apply rename only for existing columns
            actual_rename = {k: v for k, v in rename_map.items() if k in self.data.columns}
            self.data = self.data.rename(columns=actual_rename)
            
            print(f"After rename - Columns: {list(self.data.columns)}")

            # Column 0 -------> Date
            if 'Date' in self.data.columns:
                try:
                    self.convert_date('Date')
                    # Extract date only (remove time if present)
                    self.data['Date'] = pd.to_datetime(self.data['Date']).dt.date
                    self.data['Date'] = pd.to_datetime(self.data['Date'])
                except:
                    self.data['Date'] = pd.NaT

            # Add Sales price if missing or convert to numeric
            if 'Sales price' in self.data.columns:
                self.data['Sales price'] = pd.to_numeric(self.data['Sales price'], errors='coerce').fillna(0)
            else:
                self.data['Sales price'] = 0

            # Add date-related columns
            if 'Date' in self.data.columns and pd.notna(self.data['Date']).any():
                self.data.insert(1, 'Month', self.data['Date'].dt.strftime('%B'))
                self.data.insert(2, 'Month Number', self.data['Date'].dt.month)
                self.data.insert(3, 'Year', self.data['Date'].dt.year)
            else:
                self.data.insert(1, 'Month', '')
                self.data.insert(2, 'Month Number', '')
                self.data.insert(3, 'Year', '')

            # Add Nub Partner if Partner ID exists
            if 'Partner ID' in self.data.columns:
                self.data.insert(8, 'Nub Partner', self.data['Partner ID'].apply(self.get_nub_partner))
            else:
                self.data.insert(8, 'Nub Partner', '')

            # ✅ FIX: Add Brand, Category, Sub-Category in correct positions
            # Current columns: 0: Date, 1: Month, 2: Month Number, 3: Year, 
            # 4: Order Number, 5: SKU, 6: Status, 7: Partner ID, 8: Nub Partner, 9: Country
            
            # Column 10 -----> Brand Name
            self.data.insert(10, 'Brand Name', "")
            
            # Column 11 -----> Category
            self.data.insert(11, 'Category', "")
            
            # Column 12 -----> Sub-Category
            self.data.insert(12, 'Sub-Category', "")
            
            # Add remaining columns in correct order
            col_index = 13
            
            # Channel
            if 'Channel' in self.data.columns:
                if 'Channel' not in [self.data.columns[col_index]]:
                    channel_col = self.data.pop('Channel')
                    self.data.insert(col_index, 'Channel', channel_col)
                col_index += 1
            else:
                self.data.insert(col_index, 'Channel', 'Amazon')
                col_index += 1
            
            # Channel Item Name
            if 'Channel Item Name' in self.data.columns:
                if 'Channel Item Name' not in [self.data.columns[col_index]]:
                    item_name_col = self.data.pop('Channel Item Name')
                    self.data.insert(col_index, 'Channel Item Name', item_name_col)
                col_index += 1
            else:
                self.data.insert(col_index, 'Channel Item Name', "")
                col_index += 1
            
            # Partner SKU
            if 'Partner SKU' in self.data.columns:
                if 'Partner SKU' not in [self.data.columns[col_index]]:
                    partner_sku_col = self.data.pop('Partner SKU')
                    self.data.insert(col_index, 'Partner SKU', partner_sku_col)
                col_index += 1
            else:
                self.data.insert(col_index, 'Partner SKU', "")
                col_index += 1
            
            # Fulfillment
            if 'Fulfillment' in self.data.columns:
                if 'Fulfillment' not in [self.data.columns[col_index]]:
                    fulfillment_col = self.data.pop('Fulfillment')
                    self.data.insert(col_index, 'Fulfillment', fulfillment_col)
                col_index += 1
            else:
                self.data.insert(col_index, 'Fulfillment', "")
                col_index += 1
            
            # Sales price
            if 'Sales price' in self.data.columns:
                if 'Sales price' not in [self.data.columns[col_index]]:
                    price_col = self.data.pop('Sales price')
                    self.data.insert(col_index, 'Sales price', price_col)
                col_index += 1
            
            # QTY - ensure it exists
            if 'QTY' not in self.data.columns:
                self.data.insert(col_index, 'QTY', 1)
            col_index += 1
            
            # GMV
            self.data.insert(col_index, 'GMV', self.data['Sales price'] * pd.to_numeric(self.data['QTY'], errors='coerce').fillna(1))

            # Filter irrelevant statuses
            if 'Status' in self.data.columns:
                irrelevant_statuses = ['Unshipped', 'Pending', 'Undelivered', 'Confirmed', 'Created', 'Exported', 'Fulfilling']
                self.data = self.data[~self.data['Status'].isin(irrelevant_statuses)]

            # Replace values
            if 'Country' in self.data.columns:
                self.data['Country'] = self.data['Country'].replace({
                    'SA': 'Saudi', 'AE': 'UAE', 'BH': 'Bahrain', 'KW': 'Kuwait', 'OM': 'Oman',
                    'sa': 'Saudi', 'ae': 'UAE', 'bh': 'Bahrain', 'kw': 'Kuwait', 'om': 'Oman'
                })
            
            if 'Channel' in self.data.columns:
                self.data['Channel'] = self.data['Channel'].replace({
                    'Amazon.ae': 'Amazon', 'Amazon.sa': 'Amazon', 'Amazon.eg': 'Amazon',
                    'amazon.ae': 'Amazon', 'amazon.sa': 'Amazon'
                })
            
            if 'Status' in self.data.columns:
                self.data['Status'] = self.data['Status'].replace({'Shipped': 'Delivered'})
            
            if 'Fulfillment' in self.data.columns:
                self.data['Fulfillment'] = self.data['Fulfillment'].replace({
                    'Amazon': 'FBA', 'amazon': 'FBA', 'Amazon.com': 'FBA'
                })

            # Fill from master data if available
            if not self.master_df.empty and 'SKU' in self.data.columns:
                # Clean SKU
                self.data['SKU'] = self.data['SKU'].astype(str).str.strip()
                
                # Convert blanks to NaN
                cols_to_fill = ['Brand Name', 'Category', 'Sub-Category']
                for col in cols_to_fill:
                    if col in self.data.columns:
                        self.data[col] = self.data[col].replace(r'^\s*$', np.nan, regex=True)
                
                # Merge with master data (using SKU)
                if 'SKU' in self.master_df.columns or 'Partner SKU' in self.master_df.columns:
                    # Try SKU first
                    if 'SKU' in self.master_df.columns:
                        master_subset = self.master_df[['SKU', 'Brand', 'Category', 'Sub-Category']].copy()
                        master_subset.columns = ['SKU', 'Brand_master', 'Category_master', 'Sub-Category_master']
                        
                        self.data = self.data.merge(
                            master_subset,
                            on='SKU',
                            how='left'
                        )
                    
                    # If no match, try Partner SKU
                    elif 'Partner SKU' in self.master_df.columns and 'Partner SKU' in self.data.columns:
                        master_subset = self.master_df[['Partner SKU', 'Brand', 'Category', 'Sub-Category']].copy()
                        master_subset.columns = ['Partner SKU', 'Brand_master', 'Category_master', 'Sub-Category_master']
                        
                        self.data = self.data.merge(
                            master_subset,
                            left_on='SKU',
                            right_on='Partner SKU',
                            how='left'
                        )
                    
                    # Fill empty values from master
                    if 'Brand_master' in self.data.columns:
                        self.data['Brand Name'] = self.data['Brand Name'].fillna(self.data['Brand_master'])
                    
                    if 'Category_master' in self.data.columns:
                        self.data['Category'] = self.data['Category'].fillna(self.data['Category_master'])
                    
                    if 'Sub-Category_master' in self.data.columns:
                        self.data['Sub-Category'] = self.data['Sub-Category'].fillna(self.data['Sub-Category_master'])
                    
                    # Drop helper columns
                    columns_to_drop = ['Brand_master', 'Category_master', 'Sub-Category_master']
                    if 'Partner SKU_y' in self.data.columns:
                        columns_to_drop.append('Partner SKU_y')
                    
                    for col in columns_to_drop:
                        if col in self.data.columns:
                            self.data = self.data.drop(columns=[col])
                    
                    # Rename Partner SKU_x back if needed
                    if 'Partner SKU_x' in self.data.columns:
                        self.data = self.data.rename(columns={'Partner SKU_x': 'Partner SKU'})

            # Set QTY = 1 for cancelled orders
            if 'Status' in self.data.columns and 'QTY' in self.data.columns:
                self.data.loc[
                    self.data['Status'].astype(str).str.strip().str.upper() == 'CANCELLED', 'QTY'] = 1

            # Fill NaN values with empty string
            self.data = self.data.fillna('')
            
            # Ensure correct column order
            expected_columns = ['Date', 'Month', 'Month Number', 'Year', 'Order Number', 'SKU', 
                              'Status', 'Partner ID', 'Nub Partner', 'Country', 'Brand Name',
                              'Category', 'Sub-Category', 'Channel', 'Channel Item Name',
                              'Partner SKU', 'Fulfillment', 'Sales price', 'QTY', 'GMV']
            
            # Add any missing columns
            for col in expected_columns:
                if col not in self.data.columns:
                    self.data[col] = ''
            
            # Reorder columns
            self.data = self.data[expected_columns]
            
            print(f"Amazon Cleaned Data Shape: {self.data.shape}")
            print(f"Amazon Columns: {list(self.data.columns)}")

        except Exception as e:
            print(f"Error Cleaning Amazon Data: {e}")
            import traceback
            traceback.print_exc()
            raise e

    def get_nub_partner(self, pid):
        pid_str = str(pid).strip()
        if pid_str == 'Wishcare':
            return 'Nub-Partner Wishcare'
        elif pid_str == '100 MPH':
            return 'Nub-Partner 100 MPH'
        elif pid_str == '100_Miles':
            return 'Nub-Partner 100_Miles'
        else:
            return 'Null'

# Rest of the classes remain the same...
# [RevibeCleaner, TalabatCleaner, CareemCleaner unchanged]

# Revibe Cleaner - FIXED
class RevibeCleaner(BaseCleaner):
    def clean(self):
        try:
            self.read_data()
            
            # Check required columns
            required_columns = ['Last Update Date', 'id', 'SKU (Old: Order Status)', 'Shipment Status',
                               'Supplier', 'Country', 'Category', 'Condition', 'Model',
                               'Variation: Color, Storage, Condition', 'Actual Cost']
            
            existing_columns = [col for col in required_columns if col in self.data.columns]
            self.data = self.data[existing_columns]

            # Rename columns
            rename_map = {
                'Last Update Date': 'Date',
                'id': 'Order Number',
                'SKU (Old: Order Status)': 'SKU',
                'Shipment Status': 'Status',
                'Supplier': 'Partner Id',
                'Condition': 'Sub-Category',
                'Actual Cost': 'Sales Price'
            }
            
            actual_rename = {k: v for k, v in rename_map.items() if k in self.data.columns}
            self.data = self.data.rename(columns=actual_rename)

            # Convert date
            if 'Date' in self.data.columns:
                try:
                    self.convert_date1('Date')
                    self.data['Date'] = pd.to_datetime(self.data['Date'])
                    self.data['Date'] = pd.to_datetime(self.data['Date'].dt.date)
                except:
                    self.data['Date'] = pd.NaT

            # Add date columns
            if 'Date' in self.data.columns:
                self.data.insert(1, 'Month', self.data['Date'].dt.strftime('%B'))
                self.data.insert(2, 'Month Number', self.data['Date'].dt.month)
                self.data.insert(3, 'Year', self.data['Date'].dt.year)
            else:
                self.data.insert(1, 'Month', '')
                self.data.insert(2, 'Month Number', '')
                self.data.insert(3, 'Year', '')

            # Add Nub Partner
            if 'Partner Id' in self.data.columns:
                self.data.insert(8, 'Nub-Partner', 'Revibe ' + self.data['Partner Id'].astype(str))
            else:
                self.data.insert(8, 'Nub-Partner', '')
            
            # Add Brand Name
            self.data.insert(10, 'Brand Name', 'Apple')
            
            # Add Channel
            self.data.insert(13, 'Channel', 'Revibe')
            
            # Add Channel Item Name
            if 'Model' in self.data.columns and 'Variation: Color, Storage, Condition' in self.data.columns:
                self.data.insert(14, 'Channel Item Name', 
                               self.data['Model'] + ' ' + self.data['Variation: Color, Storage, Condition'])
            else:
                self.data.insert(14, 'Channel Item Name', '')
            
            # Add Partner SKU
            if 'SKU' in self.data.columns:
                self.data.insert(15, 'Partner SKU', self.data['SKU'])
            else:
                self.data.insert(15, 'Partner SKU', '')
            
            # Add Fulfillment
            self.data.insert(16, 'Fulfillment', 'FBR')
            
            # Add QTY and GMV
            self.data.insert(20, 'QTY', 1)
            
            if 'Sales Price' in self.data.columns:
                self.data.insert(21, 'GMV', self.data['Sales Price'] * self.data['QTY'])
            else:
                self.data.insert(21, 'GMV', 0)

            # Drop unnecessary columns
            columns_to_drop = ['Model', 'Variation: Color, Storage, Condition']
            for col in columns_to_drop:
                if col in self.data.columns:
                    self.data = self.data.drop(columns=[col])

            # Standardize values
            if 'Status' in self.data.columns:
                self.data['Status'] = self.data['Status'].replace({
                    'Shipped': 'Delivered',
                    'At quality check': 'Delivered',
                    'Refused delivery': 'Delivered'
                })
            
            if 'Country' in self.data.columns:
                self.data['Country'] = self.data['Country'].replace({'United Arab Emirates': 'UAE'})

            # Sort by Date if available
            if 'Date' in self.data.columns:
                self.data = self.data.sort_values(by='Date', ascending=True)

            # Fill NaN values
            self.data = self.data.fillna('')
            
            print(f"Revibe Cleaned Data Shape: {self.data.shape}")
            
        except Exception as e:
            print(f"Error Cleaning Revibe Data: {e}")
            raise e

class TalabatCleaner(BaseCleaner):
    def clean(self):
        try:
            self.read_data()
            print("Talabat cleaning not implemented yet.")
            # Create basic structure
            self.data['Channel'] = 'Talabat'
            self.data['QTY'] = 1
            self.data['GMV'] = 0
        except Exception as e:
            print(f"Error Cleaning Talabat Data: {e}")

class CareemCleaner(BaseCleaner):
    def clean(self):
        try:
            self.read_data()
            print("Careem cleaning not implemented yet.")
            # Create basic structure
            self.data['Channel'] = 'Careem'
            self.data['QTY'] = 1
            self.data['GMV'] = 0
        except Exception as e:
            print(f"Error Cleaning Careem Data: {e}")

# Example Usage
if __name__ == "__main__":
    # Test Noon
    noon = NoonCleaner("Noon_Sales_Data.csv")
    noon.clean()
    noon.save_data("Clean_Noon_Data.csv")
    
    # Test Amazon
    amazon = AmazonCleaner("Amazon_Sales_Data.xlsx")
    amazon.clean()
    amazon.save_data("Clean_Amazon_Data.csv")
    
    # Test Revibe
    revibe = RevibeCleaner("Revibe_Sales_Data.csv")
    revibe.clean()
    revibe.save_data("Clean_Revibe_Data.csv")