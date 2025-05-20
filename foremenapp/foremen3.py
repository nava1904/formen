# -*- coding: utf-8 -*-
"""
Streamlit application for Foremen Choice Digital Records Manager.
Connects to a MySQL database.
"""

import streamlit as st
import mysql.connector
from mysql.connector import Error
import uuid # Required for generating UUIDs
import datetime # Required for date/time handling
# You might need dateutil for more robust date calculations (e.g., adding months precisely)
# pip install python-dateutil
# from dateutil.relativedelta import relativedelta

# --- Database Connection ---

@st.cache_resource # Cache the database connection to avoid reconnecting on every rerun
def get_db_connection():
    """
    Establishes and caches the connection to the MySQL database.
    This function should ONLY connect and return the connection object.
    Database operations (cursor, execute, commit, fetch, close) happen elsewhere.
    Credentials are read from .streamlit/secrets.toml
    """
    try:
        # Connect to the MySQL database using credentials from Streamlit Secrets
        # Ensure you have a .streamlit/secrets.toml file with your database credentials
        # Access secrets using st.secrets["section_name"]["key_name"]
        conn = mysql.connector.connect(
            host=st.secrets["mysql"]["host"],     # Get host from secrets
            database=st.secrets["mysql"]["database"], # Get database name from secrets
            user=st.secrets["mysql"]["user"],     # Get user from secrets
            password=st.secrets["mysql"]["password"], # Get password from secrets
            # Optional: Uncomment the line below and add port if needed in secrets.toml
            # port=st.secrets["mysql"]["port"]
        )
        # Check if connection was successful
        if conn.is_connected():
            print("Successfully connected to MySQL database") # Optional: Log success
            return conn # <<< ONLY return the connection object

        else:
            # This case might occur if connect() didn't raise an exception but isn't connected
            print("Failed to connect to MySQL database (is_connected() is False)") # Optional: Log failure
            # Display error in Streamlit
            st.error("Database connection failed.")
            return None # <<< Return None if connection failed without exception

    except Error as e:
        # Handle connection errors (e.g., incorrect credentials, DB not running)
        print(f"Error connecting to MySQL database: {e}") # Optional: Log error details
        st.error(f"Database connection error: Unable to connect. Please check your credentials and database status. Details: {e}")
        return None # <<< Return None on exception

    # No finally block needed here as we are not managing cursor/transaction within this function


# --- Helper Function for Date Calculation (Simplified) ---
# Note: This is a basic function. For production, consider using the 'dateutil' library
# (install via pip install python-dateutil) for more accurate month addition,
# especially when dealing with end-of-month dates.
def add_months(sourcedate, months):
    """Adds months to a given date (simplified)."""
    import calendar
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year,month)[1])
    return datetime.date(year, month, day)
    # Alternative using dateutil:
    # from dateutil.relativedelta import relativedelta
    # return sourcedate + relativedelta(months=+months)


# --- Generic Database Interaction Functions ---
# These functions encapsulate common SQL operations.

def delete_item(table_name, item_id_bytes):
    """Deletes an item from a specified table by its ID (BINARY(16))."""
    conn = get_db_connection()
    if conn is None:
        return False

    cursor = None
    try:
        cursor = conn.cursor()
        # Use a parameterized query to prevent SQL injection
        query = f"DELETE FROM {table_name} WHERE id = %s"
        cursor.execute(query, (item_id_bytes,))
        conn.commit()
        # Check if any rows were affected to confirm deletion
        if cursor.rowcount > 0:
            st.success(f"Item deleted successfully from {table_name}!")
            return True
        else:
            st.warning(f"No item found with the specified ID in {table_name}.")
            return False
    except Error as e:
        # Handle potential foreign key constraint errors if ON DELETE CASCADE is not set up
        if e.errno == 1451: # MySQL error code for foreign key constraint failure
             st.error(f"Error deleting item from {table_name}: Cannot delete because there are related records in other tables (e.g., Enrollments, Payments). Delete those first or ensure ON DELETE CASCADE is set up.")
        else:
            st.error(f"Error deleting item from {table_name}: {e}")
            # print(f"Error deleting item from {table_name}: {e}") # Optional log
        if conn:
            conn.rollback() # Rollback changes if the transaction failed
        return False
    finally:
        if cursor:
            cursor.close()

# --- Specific Database Interaction Functions ---
# These call the generic functions or perform specific complex queries.

# --- ChitGroup Functions ---

def insert_group(name, value, num_subscribers, duration, start_date, commission):
    """Inserts a new Chit Group into the database."""
    conn = get_db_connection()
    if conn is None:
        return False # Indicate failure if connection failed

    cursor = None # Initialize cursor to None
    try:
        cursor = conn.cursor()
        # Generate a UUID for the new group
        group_id = uuid.uuid4().bytes # Use .bytes for BINARY(16) in MySQL

        # SQL query to insert data into the ChitGroups table
        query = """INSERT INTO ChitGroups (id, name, value, numberOfSubscribers, duration, startDate, foremanCommissionPercentage, isActive)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        # Prepare the values tuple, ensuring types match SQL columns
        values = (
            group_id, # BINARY(16)
            name, # VARCHAR
            value, # DOUBLE
            num_subscribers, # SMALLINT
            duration, # SMALLINT
            start_date, # DATE (Python date/datetime objects are usually handled by connector)
            commission, # DOUBLE (Optional, can be None)
            True # BOOLEAN
        )
        # Execute the query with the values
        cursor.execute(query, values)
        conn.commit() # Commit the transaction to save changes to the database
        st.success(f"Chit Group '{name}' added successfully!") # Display success message in Streamlit
        return True # Indicate success
    except Error as e:
        # Handle specific MySQL errors if needed (e.g., duplicate entry)
        # print(f"Error adding Chit Group: {e}") # Optional: Log the error
        st.error(f"Error adding Chit Group: {e}") # Display error in Streamlit
        if conn:
            conn.rollback() # Rollback changes if the transaction failed
        return False # Indicate failure
    finally:
        # Ensure the cursor is closed even if an error occurs
        if cursor:
            cursor.close()

def get_all_chit_groups():
    """Fetches all active Chit Groups from the database."""
    conn = get_db_connection()
    if conn is None:
        return [] # Return empty list if connection failed

    cursor = None
    try:
        cursor = conn.cursor(dictionary=True) # Fetch rows as dictionaries for easier access
        # SQL query to select data
        query = "SELECT id, name, value, numberOfSubscribers, duration, startDate, foremanCommissionPercentage FROM ChitGroups WHERE isActive = TRUE ORDER BY startDate DESC, name"
        cursor.execute(query)
        results = cursor.fetchall() # Fetch all rows

        # Convert id (BINARY) to UUID object for display
        for row in results:
            if isinstance(row['id'], bytes):
                row['id'] = uuid.UUID(bytes=row['id'])

        return results # Return the list of dictionaries
    except Error as e:
        # print(f"Error fetching Chit Groups: {e}") # Optional: Log the error
        st.error(f"Error fetching Chit Groups: {e}") # Display error in Streamlit
        return [] # Return empty list on error
    finally:
        if cursor:
            cursor.close()

def get_group_names_and_ids():
    """Fetches names and IDs of active Chit Groups for use in dropdowns/select boxes."""
    conn = get_db_connection()
    if conn is None:
        return []

    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT id, name FROM ChitGroups WHERE isActive = TRUE ORDER BY name"
        cursor.execute(query)
        results = cursor.fetchall()
         # Return a list of tuples [(name, id)] which is suitable for Streamlit selectbox options
        return [(group['name'], group['id']) for group in results]
    except Error as e:
        st.error(f"Error fetching group names: {e}")
        return []
    finally:
        if cursor:
            cursor.close()

def get_group_details_by_id(group_id_bytes):
    """Fetches details for a single group by its ID (BINARY(16))."""
    conn = get_db_connection()
    if conn is None:
        return None

    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT id, name, value, numberOfSubscribers, duration, startDate, foremanCommissionPercentage FROM ChitGroups WHERE id = %s"
        cursor.execute(query, (group_id_bytes,))
        result = cursor.fetchone() # Fetch a single row
        if result and isinstance(result['id'], bytes):
             result['id'] = uuid.UUID(bytes=result['id'])
        return result # Return the dictionary or None if not found
    except Error as e:
        st.error(f"Error fetching group details: {e}")
        return None
    finally:
        if cursor:
            cursor.close()


# --- Subscriber Functions ---

def insert_subscriber(name, phone, address):
    """Inserts a new Subscriber into the database."""
    conn = get_db_connection()
    if conn is None:
        return False

    cursor = None
    try:
        cursor = conn.cursor()
        subscriber_id = uuid.uuid4().bytes
        # Use NOW() or CURRENT_TIMESTAMP() in SQL, or pass Python datetime.datetime.now()
        query = """INSERT INTO Subscribers (id, name, phoneNumber, address, createdDate, isActive)
                   VALUES (%s, %s, %s, %s, %s, %s)"""
        values = (
            subscriber_id, # BINARY(16)
            name, # VARCHAR
            phone, # VARCHAR
            address, # TEXT (Optional)
            datetime.datetime.now(), # DATETIME
            True # BOOLEAN
        )
        cursor.execute(query, values)
        conn.commit()
        st.success(f"Subscriber '{name}' added successfully!")
        return True
    except Error as e:
        # Check for duplicate phone number error (MySQL error code 1062)
        if e.errno == 1062:
             st.error(f"Error adding Subscriber: Phone number '{phone}' already exists.")
        else:
            st.error(f"Error adding Subscriber: {e}")
            # print(f"Error adding Subscriber: {e}") # Optional log
        if conn: conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()


def get_all_subscribers():
    """Fetches all active Subscribers from the database."""
    conn = get_db_connection()
    if conn is None:
        return []

    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT id, name, phoneNumber, address, createdDate FROM Subscribers WHERE isActive = TRUE ORDER BY name"
        cursor.execute(query)
        results = cursor.fetchall()

        for row in results:
            if isinstance(row['id'], bytes):
                row['id'] = uuid.UUID(bytes=row['id']) # Convert bytes to UUID object

        return results
    except Error as e:
        st.error(f"Error fetching Subscribers: {e}")
        return []
    finally:
        if cursor:
            cursor.close()

def get_subscriber_names_and_ids():
    """Fetches names and IDs of active Subscribers for dropdowns."""
    conn = get_db_connection()
    if conn is None:
        return []

    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT id, name FROM Subscribers WHERE isActive = TRUE ORDER BY name"
        cursor.execute(query)
        results = cursor.fetchall()
         # Return a list of tuples [(name, id)]
        return [(sub['name'], sub['id']) for sub in results]
    except Error as e:
        st.error(f"Error fetching subscriber names: {e}")
        return []
    finally:
        if cursor:
            cursor.close()

def get_subscriber_details_by_id(subscriber_id_bytes):
     """Fetches details for a single subscriber by ID (BINARY(16))."""
     conn = get_db_connection()
     if conn is None:
         return None

     cursor = None
     try:
         cursor = conn.cursor(dictionary=True)
         query = "SELECT id, name, phoneNumber, address FROM Subscribers WHERE id = %s"
         cursor.execute(query, (subscriber_id_bytes,))
         result = cursor.fetchone()
         if result and isinstance(result['id'], bytes):
              result['id'] = uuid.UUID(bytes=result['id'])
         return result
     except Error as e:
         st.error(f"Error fetching subscriber details: {e}")
         return None
     finally:
         if cursor:
             cursor.close()


# --- Enrollment Functions ---

def insert_enrollment(subscriber_id_bytes, group_id_bytes, assigned_number, join_date):
    """Enrolls a Subscriber (by ID) in a Chit Group (by ID) with an assigned number."""
    conn = get_db_connection()
    if conn is None:
        return False

    cursor = None
    try:
        cursor = conn.cursor()
        enrollment_id = uuid.uuid4().bytes # UUID for the enrollment record

        query = """INSERT INTO Enrollments (id, subscriberId, groupId, assignedChitNumber, joinDate)
                   VALUES (%s, %s, %s, %s, %s)"""
        values = (
            enrollment_id, # BINARY(16)
            subscriber_id_bytes, # BINARY(16) - already bytes from get_subscriber_names_and_ids
            group_id_bytes,      # BINARY(16) - already bytes from get_group_names_and_ids
            assigned_number, # SMALLINT
            join_date      # DATE
        )
        cursor.execute(query, values)
        conn.commit()
        st.success("Subscriber enrolled successfully!")
        return True
    except Error as e:
        # Check for unique constraint violation (Error code 1062 for MySQL)
        if e.errno == 1062:
             st.error("Error enrolling Subscriber: Either they are already enrolled in this group, or the assigned number is already taken in this group.")
        else:
            st.error(f"Error enrolling Subscriber: {e}")
            # print(f"Error enrolling Subscriber: {e}") # Optional log
        if conn: conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()

def get_enrollments_details_for_group(group_id_bytes):
    """Fetches enrollment details (Subscriber name, number, join date) for a specific group."""
    conn = get_db_connection()
    if conn is None:
        return []

    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        # Join Enrollments with Subscribers to get subscriber names and phone numbers
        query = """SELECT
                       e.id AS enrollmentId,
                       s.id AS subscriberId,
                       s.name AS subscriberName,
                       s.phoneNumber AS subscriberPhone,
                       e.assignedChitNumber,
                       e.joinDate
                   FROM Enrollments e
                   JOIN Subscribers s ON e.subscriberId = s.id
                   WHERE e.groupId = %s
                   ORDER BY e.assignedChitNumber"""
        cursor.execute(query, (group_id_bytes,)) # Pass group_id_bytes as a tuple
        results = cursor.fetchall()

        # Convert BINARY IDs to UUID objects for display
        for row in results:
            if isinstance(row['enrollmentId'], bytes):
                row['enrollmentId'] = uuid.UUID(bytes=row['enrollmentId'])
            if isinstance(row['subscriberId'], bytes):
                row['subscriberId'] = uuid.UUID(bytes=row['subscriberId'])

        return results
    except Error as e:
        st.error(f"Error fetching enrollments: {e}")
        return []
    finally:
        if cursor:
            cursor.close()

# --- Installment Functions ---

def generate_installments_for_group(group_id_bytes, start_date, duration):
     """Generates Installment records for a group (simplified date logic)."""
     conn = get_db_connection()
     if conn is None:
         return False

     cursor = None
     try:
         cursor = conn.cursor()
         # Check if installments already exist for this group to prevent duplicates
         check_query = "SELECT COUNT(*) FROM Installments WHERE groupId = %s"
         cursor.execute(check_query, (group_id_bytes,))
         count = cursor.fetchone()[0]
         if count > 0:
             st.warning("Installments already exist for this group. Cannot regenerate.")
             return False # Indicate failure

         query = """INSERT INTO Installments (id, groupId, monthNumber, dueDate, isAuctionConducted, isCompleted)
                    VALUES (%s, %s, %s, %s, %s, %s)"""
         values_to_insert = []
         # Ensure start_date is a datetime.date object before date calculation
         if not isinstance(start_date, datetime.date):
             if isinstance(start_date, datetime.datetime):
                 start_date = start_date.date() # Convert if it's a datetime
             else:
                 st.error("Invalid start date type provided for installment generation.")
                 return False

         # Generate installment dates and data
         for month_num in range(1, duration + 1):
             installment_id = uuid.uuid4().bytes
             # Calculate due date: Month 1 is due on start_date, Month 2 is start_date + 1 month, etc.
             # Use the add_months helper function (or a more robust library)
             due_date = add_months(start_date, month_num - 1) # Month 1 (index 0) needs 0 months added, Month 2 (index 1) needs 1 month, etc.

             values_to_insert.append((installment_id, group_id_bytes, month_num, due_date, False, False))

         # Use executemany for efficient bulk insertion
         cursor.executemany(query, values_to_insert)
         conn.commit()
         st.success(f"Generated {duration} installments for the group.")
         return True
     except Error as e:
         st.error(f"Error generating installments: {e}")
         # print(f"Error generating installments: {e}") # Optional log
         if conn: conn.rollback()
         return False
     finally:
         if cursor:
             cursor.close()


def get_installments_for_group(group_id_bytes):
     """Fetches installments for a specific group."""
     conn = get_db_connection()
     if conn is None:
         return []

     cursor = None
     try:
         cursor = conn.cursor(dictionary=True)
         query = """SELECT
                        id,
                        groupId,
                        monthNumber,
                        dueDate,
                        isAuctionConducted,
                        auctionPrizeAmount,
                        auctionWinnerId,
                        isCompleted
                    FROM Installments
                    WHERE groupId = %s
                    ORDER BY monthNumber"""
         cursor.execute(query, (group_id_bytes,))
         results = cursor.fetchall()

         # Convert BINARY IDs to UUID objects
         for row in results:
             if isinstance(row['id'], bytes):
                 row['id'] = uuid.UUID(bytes=row['id'])
             if isinstance(row['groupId'], bytes):
                  row['groupId'] = uuid.UUID(bytes=row['groupId'])
             if row['auctionWinnerId'] and isinstance(row['auctionWinnerId'], bytes):
                 row['auctionWinnerId'] = uuid.UUID(bytes=row['auctionWinnerId'])


         return results
     except Error as e:
         st.error(f"Error fetching installments: {e}")
         return []
     finally:
         if cursor:
             cursor.close()

def update_installment_auction(installment_id_bytes, prize_amount, winner_subscriber_id_bytes):
    """Updates an installment with auction details (prize amount and winner)."""
    conn = get_db_connection()
    if conn is None:
        return False

    cursor = None
    try:
        cursor = conn.cursor()
        query = """UPDATE Installments
                   SET isAuctionConducted = TRUE, auctionPrizeAmount = %s, auctionWinnerId = %s
                   WHERE id = %s"""
        values = (
            prize_amount, # DOUBLE
            winner_subscriber_id_bytes, # BINARY(16)
            installment_id_bytes # BINARY(16)
        )
        cursor.execute(query, values)
        conn.commit()
        if cursor.rowcount > 0:
            st.success("Auction details updated successfully!")
            return True
        else:
            st.warning("No installment found with the specified ID to update.")
            return False
    except Error as e:
        st.error(f"Error updating auction details: {e}")
        # print(f"Error updating auction details: {e}") # Optional log
        if conn: conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()


# --- InstallmentPayment Functions ---
# (Requires selecting Installment and Subscriber to record payment)

def insert_payment(installment_id_bytes, subscriber_id_bytes, amount_paid, notes):
    """Records a payment for an installment by a subscriber."""
    conn = get_db_connection()
    if conn is None:
        return False

    cursor = None
    try:
        cursor = conn.cursor()
        payment_id = uuid.uuid4().bytes # UUID for the payment record

        query = """INSERT INTO InstallmentPayments (id, installmentId, subscriberId, paymentDate, amountPaid, notes)
                   VALUES (%s, %s, %s, %s, %s, %s)"""
        values = (
            payment_id, # BINARY(16)
            installment_id_bytes, # BINARY(16)
            subscriber_id_bytes, # BINARY(16)
            datetime.datetime.now(), # DATETIME (Record the exact time of payment entry)
            amount_paid, # DOUBLE
            notes # TEXT (Optional)
        )
        cursor.execute(query, values)
        conn.commit()
        st.success("Payment recorded successfully!")
        # TODO: Add logic here to update related records if needed (e.g., mark installment as paid for this subscriber)
        return True
    except Error as e:
        st.error(f"Error recording payment: {e}")
        # print(f"Error recording payment: {e}") # Optional log
        if conn: conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()

def get_payments_for_installment(installment_id_bytes):
    """Fetches payments recorded for a specific installment."""
    conn = get_db_connection()
    if conn is None:
        return []

    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        # Join with Subscribers to show who paid
        query = """SELECT
                       ip.id AS paymentId,
                       s.name AS subscriberName,
                       ip.paymentDate,
                       ip.amountPaid,
                       ip.notes
                   FROM InstallmentPayments ip
                   JOIN Subscribers s ON ip.subscriberId = s.id
                   WHERE ip.installmentId = %s
                   ORDER BY ip.paymentDate"""
        cursor.execute(query, (installment_id_bytes,))
        results = cursor.fetchall()

        # Convert BINARY IDs to UUID objects
        for row in results:
             if isinstance(row['paymentId'], bytes):
                  row['paymentId'] = uuid.UUID(bytes=row['paymentId'])

        return results
    except Error as e:
        st.error(f"Error fetching payments for installment: {e}")
        return []
    finally:
        if cursor:
            cursor.close()

# --- Dues & Status Functions ---
# (More complex - involves comparing enrollments, installments, and payments)

def get_payment_status_for_installment(group_id_bytes, installment_month_number):
    """
    Gets payment status for all enrolled subscribers for a specific installment (by group and month number).
    This version fetches total paid for the installment by each subscriber.
    Exact 'Due' amount calculation depends on specific chit fund rules (auction, commission).
    """
    conn = get_db_connection()
    if conn is None:
        return []

    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)

        # First, find the installment ID for the given group and month number
        cursor.execute("SELECT id FROM Installments WHERE groupId = %s AND monthNumber = %s", (group_id_bytes, installment_month_number))
        installment_row = cursor.fetchone()
        if not installment_row:
            st.info(f"Installment Month {installment_month_number} not found for this group.")
            return []
        installment_id_bytes = installment_row['id']

        # Fetch total amount paid by each subscriber for this specific installment
        # Use GROUP BY and SUM to handle multiple payments by one subscriber for the same installment
        query = """
            SELECT
                e.id AS enrollmentId,
                s.id AS subscriberId,
                s.name AS subscriberName,
                e.assignedChitNumber,
                SUM(ip.amountPaid) AS totalPaidThisInstallment -- Sum payments for this installment
            FROM Enrollments e
            JOIN Subscribers s ON e.subscriberId = s.id
            LEFT JOIN InstallmentPayments ip
                ON e.subscriberId = ip.subscriberId AND ip.installmentId = %s
            WHERE e.groupId = %s
            GROUP BY e.id, s.id, s.name, e.assignedChitNumber -- Group by enrollment details
            ORDER BY e.assignedChitNumber;
        """
        cursor.execute(query, (installment_id_bytes, group_id_bytes))
        results = cursor.fetchall()

        # Process results to determine status (Simplified: Paid if total paid > 0, Due otherwise)
        # You would add logic here to calculate expected amount and compare.
        status_list = []
        for row in results:
            total_paid = row['totalPaidThisInstallment'] if row['totalPaidThisInstallment'] is not None else 0
            status = "Paid" if total_paid > 0 else "Due"
            # TODO: Implement logic to calculate 'Expected Amount' and determine 'Partial' or 'Overdue' status

            status_list.append({
                "Subscriber Name": row['subscriberName'],
                "Chit Number": row['assignedChitNumber'],
                "Status": status,
                "Total Paid (This Installment)": total_paid,
                # TODO: Add 'Expected Amount' and 'Balance Due' columns based on your rules
            })

        return status_list # Return list of status dictionaries


    except Error as e:
        st.error(f"Error fetching payment status: {e}")
        # print(f"Error fetching payment status: {e}") # Optional log
        return []
    finally:
        if cursor:
            cursor.close()


# --- Streamlit App Layout ---

st.title("DHARMAREDDY - Digital Records")

# --- Sidebar Navigation ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", [
    "Dashboard",
    "Manage Chit Groups",
    "Manage Subscribers",
    "Manage Enrollments",
    "Manage Installments",
    "Record Payments",
    "View Dues & Status"
])

# --- Page Content Based on Selection ---

if page == "Dashboard":
    st.header("Dashboard")
    st.write("Welcome to DHARMAREDDY's Digital Records Manager.")
    st.write("Use the sidebar on the left to navigate to different sections.")

    # --- Quick Stats (Requires DB queries) ---
    st.subheader("Quick Stats")
    # Get the cached connection *within* the Dashboard section
    conn = get_db_connection() # <<< Call get_db_connection() here

    if conn: # Check if the connection object is valid (not None)
         cursor = None
         try:
             cursor = conn.cursor()
             # Fetch counts of active groups and subscribers
             cursor.execute("SELECT COUNT(*) FROM ChitGroups WHERE isActive = TRUE")
             num_groups = cursor.fetchone()[0]
             cursor.execute("SELECT COUNT(*) FROM Subscribers WHERE isActive = TRUE")
             num_subscribers = cursor.fetchone()[0]

             # Display the stats using st.columns for layout
             col1, col2 = st.columns(2)
             col1.metric("Total Groups", num_groups)
             col2.metric("Total Subscribers", num_subscribers)

         except Error as e:
             # Handle errors during the stats query
             st.warning(f"Could not fetch stats: {e}")
             # Optional: Add a more user-friendly message or hide stats section
         finally:
             # Always close the cursor
             if cursor: cursor.close()
    else:
         # The database connection error message is handled within get_db_connection()
         # No additional message needed here if connection failed
         pass


elif page == "Manage Chit Groups":
    # --- Manage Chit Groups Section ---
    st.header("Manage Chit Groups")

    # --- Add New Group Form ---
    st.subheader("Add New Chit Group")
    # Use st.form for better input handling (prevents reruns on every character typed)
    with st.form("add_group_form"):
        name = st.text_input("Group Name", key="group_name_input")
        # Use number_input for numeric values
        value = st.number_input("Total Value", min_value=0.0, format="%.2f", key="group_value_input")
        num_subscribers = st.number_input("Number of Subscribers", min_value=0, step=1, key="group_sub_count_input")
        duration = st.number_input("Duration (in months)", min_value=0, step=1, key="group_duration_input")
        start_date = st.date_input("Start Date", key="group_start_date_input")
        # Commission is optional, allow None by not setting min_value and checking input string
        commission_str = st.text_input("Foreman Commission (%) (Optional)", key="group_commission_input")
        # Convert to float or None, handle potential ValueError if input is not a valid number
        try:
             commission = float(commission_str) if commission_str else None
        except ValueError:
             st.warning("Invalid input for Commission. Please enter a number.")
             commission = None # Set to None if invalid

        submitted = st.form_submit_button("Add Group")
        if submitted:
            # Perform basic validation before calling the DB function
            if name and value > 0 and num_subscribers > 0 and duration > 0 and start_date:
                # Call the database function to insert the new group
                insert_group(name, value, num_subscribers, duration, start_date, commission)
                # Optional: After adding group, maybe offer to generate installments immediately
                # if success and st.button("Generate Installments Now?", key="generate_installments_after_add"):
                #    # Need to get the ID of the newly created group to generate installments for it
                #    # This requires fetching the group back or modifying insert_group to return the ID
                #    pass # Placeholder
            else:
                st.warning("Please fill all required fields (Name, Value, Subscribers, Duration, Start Date) with valid values.")


    st.markdown("---") # Horizontal rule separator

    # --- View Existing Groups ---
    st.subheader("Existing Chit Groups")
    groups = get_all_chit_groups() # Fetch groups using the DB function
    if groups:
        # Display the list of groups in a Streamlit dataframe (interactive table)
        st.dataframe(
            groups,
            use_container_width=True, # Make dataframe use full container width
            column_config={
                "id": None, # Hide the internal ID column
                "name": "Group Name",
                "value": st.column_config.NumberColumn("Total Value", format="₹%.2f"), # Format as currency
                "numberOfSubscribers": "Subscribers",
                "duration": "Duration (Months)",
                "startDate": st.column_config.DateColumn("Start Date", format="YYYY-MM-DD"), # Format date
                "foremanCommissionPercentage": st.column_config.NumberColumn("Commission (%)", format="%.2f"),
                # Add more column configs as needed
            }
        )

        st.markdown("---") # Separator

        # --- Delete Group Section ---
        st.subheader("Delete Chit Group")
        # Create a list of group names for the selectbox
        group_names = [g['name'] for g in groups]
        selected_group_name_to_delete = st.selectbox("Select Group to Delete", group_names, key="select_group_to_delete")

        if selected_group_name_to_delete:
             # Find the ID (BINARY) of the selected group based on the name
             selected_group_id_to_delete_bytes = next((g['id'].bytes for g in groups if g['name'] == selected_group_name_to_delete), None)

             if selected_group_id_to_delete_bytes:
                  # Add a confirmation checkbox before allowing deletion
                  confirm_delete = st.checkbox(f"Yes, I am sure I want to delete '{selected_group_name_to_delete}' and all related records (enrollments, installments, payments).")

                  if confirm_delete:
                       if st.button(f"Confirm and Delete '{selected_group_name_to_delete}'"):
                            # Call the generic delete function
                            if delete_item("ChitGroups", selected_group_id_to_delete_bytes):
                                 st.rerun() # Rerun to refresh the list after deletion
                            # Error message is handled within delete_item function
                  else:
                       st.info("Check the box to confirm deletion.")
             else:
                  st.warning("Could not find the selected group ID for deletion.")


    else:
         if get_db_connection() is not None:
            st.info("No Chit Groups found in the database. Add one using the form above.")


elif page == "Manage Subscribers":
    st.header("Manage Subscribers")

    # --- Add New Subscriber Form ---
    st.subheader("Add New Subscriber")
    with st.form("add_subscriber_form"):
        name = st.text_input("Name", key="sub_name_input")
        phone = st.text_input("Phone Number", key="sub_phone_input")
        address = st.text_area("Address (Optional)", key="sub_address_input")

        submitted = st.form_submit_button("Add Subscriber")
        if submitted:
            # Basic validation
            if name and phone: # Name and Phone are required
                # Call the database function to insert the new subscriber
                insert_subscriber(name, phone, address)
            else:
                st.warning("Please fill in the Subscriber's Name and Phone Number.")

    st.markdown("---") # Separator

    # --- View Existing Subscribers ---
    st.subheader("Existing Subscribers")
    subscribers = get_all_subscribers() # Fetch subscribers using the DB function
    if subscribers:
        # Display the list of subscribers in a Streamlit dataframe
        st.dataframe(
             subscribers,
             use_container_width=True,
             column_config={
                 "id": None, # Hide internal ID
                 "name": "Name",
                 "phoneNumber": "Phone Number",
                 "address": "Address",
                 "createdDate": st.column_config.DatetimeColumn("Created Date", format="YYYY-MM-DD HH:mm") # Format datetime
             }
        )

        st.markdown("---") # Separator

        # --- Delete Subscriber Section ---
        st.subheader("Delete Subscriber")
        # Create a list of subscriber names for the selectbox
        subscriber_names = [s['name'] for s in subscribers]
        selected_subscriber_name_to_delete = st.selectbox("Select Subscriber to Delete", subscriber_names, key="select_subscriber_to_delete")

        if selected_subscriber_name_to_delete:
            # Find the ID (BINARY) of the selected subscriber based on the name
            selected_subscriber_id_to_delete_bytes = next((s['id'].bytes for s in subscribers if s['name'] == selected_subscriber_name_to_delete), None)

            if selected_subscriber_id_to_delete_bytes:
                 # Add a confirmation checkbox
                 confirm_delete_sub = st.checkbox(f"Yes, I am sure I want to delete '{selected_subscriber_name_to_delete}' and all related records (enrollments, payments).")

                 if confirm_delete_sub:
                      if st.button(f"Confirm and Delete '{selected_subscriber_name_to_delete}'"):
                           # Call the generic delete function
                           if delete_item("Subscribers", selected_subscriber_id_to_delete_bytes):
                                st.rerun() # Rerun to refresh the list
                           # Error message is handled within delete_item function
                 else:
                      st.info("Check the box to confirm deletion.")
            else:
                 st.warning("Could not find the selected subscriber ID for deletion.")


    else:
         if get_db_connection() is not None:
            st.info("No Subscribers found in the database. Add one using the form above.")


elif page == "Manage Enrollments":
    st.header("Manage Enrollments")
    st.write("Link Subscribers to specific Chit Groups with their assigned slot number.")

    # --- Add New Enrollment Form ---
    st.subheader("Enroll Subscriber in Group")
    # Get lists of groups and subscribers for the dropdowns
    group_options = get_group_names_and_ids()
    subscriber_options = get_subscriber_names_and_ids()

    # Prepare display names and create mappings from name back to ID (BINARY)
    group_display_options = [name for name, id in group_options]
    subscriber_display_options = [name for name, id in subscriber_options]
    group_id_map = {name: id for name, id in group_options}
    subscriber_id_map = {name: id for name, id in subscriber_options}

    # Check if there are groups and subscribers available to enroll
    if not group_display_options or not subscriber_display_options:
        st.info("Please add at least one Group and one Subscriber before creating enrollments.")
    else:
        with st.form("add_enrollment_form"):
            # Use selectbox to choose a group and a subscriber
            selected_group_name = st.selectbox("Select Group", group_display_options, key="enroll_group_select")
            selected_subscriber_name = st.selectbox("Select Subscriber", subscriber_display_options, key="enroll_sub_select")

            # Input for the assigned number within the group
            assigned_number = st.number_input("Assigned Chit Number", min_value=1, step=1, key="enroll_number_input")

            # Input for the date of enrollment
            join_date = st.date_input("Join Date", key="enroll_join_date_input")

            submitted = st.form_submit_button("Enroll Subscriber")
            if submitted:
                # Get the actual BINARY IDs based on the selected names
                selected_group_id_bytes = group_id_map.get(selected_group_name)
                selected_subscriber_id_bytes = subscriber_id_map.get(selected_subscriber_name)

                # Perform basic validation
                if selected_group_id_bytes and selected_subscriber_id_bytes and assigned_number >= 1 and join_date:
                    # Call the database function to insert the enrollment record
                    insert_enrollment(selected_subscriber_id_bytes, selected_group_id_bytes, assigned_number, join_date)
                else:
                    st.warning("Please select a Group and Subscriber and provide a valid Assigned Number and Join Date.")

    st.markdown("---") # Separator

    # --- View Enrollments for a Selected Group ---
    st.subheader("View Enrollments by Group")
    if group_display_options: # Check if there are groups to select from
        # Use selectbox outside form for immediate display update
        selected_group_to_view_enrollments_name = st.selectbox(
            "Select Group to View Enrollments",
            group_display_options,
            key="view_enrollments_group_select_auto"
        )

        # Check if a group is selected
        if selected_group_to_view_enrollments_name:
            # Get the ID of the selected group
            group_id_for_view_bytes = group_id_map.get(selected_group_to_view_enrollments_name)
            if group_id_for_view_bytes:
                # Fetch enrollment details for the selected group immediately
                st.subheader(f"Enrollments for {selected_group_to_view_enrollments_name}") # Add a specific subheader
                enrollments = get_enrollments_details_for_group(group_id_for_view_bytes)
                if enrollments:
                    # Display the enrollments in a dataframe with improved formatting
                    st.dataframe(
                        enrollments,
                        use_container_width=True,
                        column_config={
                            "enrollmentId": None, # Hide internal ID
                            "subscriberId": None, # Hide internal ID
                            "subscriberName": "Subscriber Name",
                            "subscriberPhone": "Phone Number",
                            "assignedChitNumber": st.column_config.NumberColumn("Chit No."),
                            "joinDate": st.column_config.DateColumn("Join Date", format="YYYY-MM-DD"),
                        }
                    )
                else:
                     st.info(f"No enrollments found for '{selected_group_to_view_enrollments_name}'.")
            else:
                st.warning("Could not find the selected group ID.")
    else:
         if get_db_connection() is not None:
            st.info("Add a group first to view enrollments.")


elif page == "Manage Installments":
    st.header("Manage Installments")
    st.write("Generate and view monthly installments for groups. Record auction details.")

    # --- Generate Installments ---
    st.subheader("Generate Installments for a Group")
    group_options_generate = get_group_names_and_ids()
    group_display_options_generate = [name for name, id in group_options_generate]
    group_id_map_generate = {name: id for name, id in group_options_generate}

    if not group_display_options_generate:
        st.info("Add a group first to generate installments.")
    else:
        selected_group_name_generate = st.selectbox("Select Group to Generate Installments", group_display_options_generate, key="generate_installments_group_select")
        generate_button = st.button("Generate Installments", key="generate_installments_button")

        if generate_button and selected_group_name_generate:
            selected_group_id_generate_bytes = group_id_map_generate.get(selected_group_name_generate)
            if selected_group_id_generate_bytes:
                # Need to fetch group details (startDate, duration) to generate installments correctly
                group_details = get_group_details_by_id(selected_group_id_generate_bytes)
                if group_details and group_details['startDate'] and group_details['duration'] > 0:
                     start_date = group_details['startDate'] # Should be datetime.date
                     duration = group_details['duration'] # Should be Int16
                     # Call the database function to generate installments
                     generate_installments_for_group(selected_group_id_generate_bytes, start_date, duration)
                else:
                     st.warning("Could not fetch required details (Start Date or Duration) for the selected group.")
            else:
                st.warning("Could not find the selected group ID.")

    st.markdown("---") # Separator

    # --- View Installments ---
    st.subheader("View Installments by Group")
    group_options_view_install = get_group_names_and_ids()
    group_display_options_view_install = [name for name, id in group_options_view_install]
    group_id_map_view_install = {name: id for name, id in group_options_view_install}

    selected_group_name_view_install = None # Initialize to None

    if not group_display_options_view_install:
         st.info("Add a group first to view installments.")
    else:
        # Selectbox outside form for immediate display
        selected_group_name_view_install = st.selectbox(
            "Select Group to View Installments & Record Auction",
            group_display_options_view_install,
            key="view_installments_group_select_auto"
        )

        # Check if a group is selected
        if selected_group_name_view_install:
            group_id_for_view_install_bytes = group_id_map_view_install.get(selected_group_name_view_install)
            if group_id_for_view_install_bytes:
                # Fetch installments for the selected group
                installments = get_installments_for_group(group_id_for_view_install_bytes)
                if installments:
                    st.subheader(f"Installments for {selected_group_name_view_install}")
                    # Display the installments in a dataframe with improved formatting
                    st.dataframe(
                        installments,
                        use_container_width=True,
                        column_config={
                            "id": None, # Hide internal ID
                            "groupId": None, # Hide internal ID
                            "monthNumber": "Month",
                            "dueDate": st.column_config.DateColumn("Due Date", format="YYYY-MM-DD"),
                            "isAuctionConducted": "Auction Held?",
                            "auctionPrizeAmount": st.column_config.NumberColumn("Auction Prize", format="₹%.2f"),
                            "auctionWinnerId": None, # Hide internal ID - display winner name below if needed
                            "isCompleted": "Completed?"
                        }
                    )

                    st.markdown("---") # Separator

                    # --- Record Auction Details Section ---
                    st.subheader("Record Auction Details")
                    # Filter for installments where auction hasn't been conducted yet
                    open_installments = [inst for inst in installments if not inst['isAuctionConducted']]
                    if open_installments:
                        # Create options for installment selectbox (only open ones)
                        installment_options_auction = [(f"Month {inst['monthNumber']} (Due: {inst['dueDate'].strftime('%Y-%m-%d')})", inst['id']) for inst in open_installments]
                        installment_display_options_auction = [name for name, id in installment_options_auction]
                        installment_id_map_auction = {name: id for name, id in installment_options_auction}

                        # Get enrolled subscribers for this group to select the winner
                        enrolled_subscribers_for_group = get_enrollments_details_for_group(group_id_for_view_install_bytes)
                        if enrolled_subscribers_for_group:
                            # Create options for subscriber selectbox
                            subscriber_options_auction = [(f"{sub['subscriberName']} (Chit No: {sub['assignedChitNumber']})", sub['subscriberId']) for sub in enrolled_subscribers_for_group]
                            subscriber_display_options_auction = [name for name, id in subscriber_options_auction]
                            subscriber_id_map_auction = {name: id for name, id in subscriber_options_auction}

                            with st.form("record_auction_form"):
                                selected_installment_name_auction = st.selectbox("Select Installment Month for Auction", installment_display_options_auction, key="auction_install_select")
                                auction_prize_amount = st.number_input("Auction Prize Amount", min_value=0.0, format="%.2f", key="auction_prize_input")
                                selected_winner_name_auction = st.selectbox("Select Auction Winner", subscriber_display_options_auction, key="auction_winner_select")

                                record_auction_button = st.form_submit_button("Record Auction Details")

                                if record_auction_button:
                                    selected_installment_id_auction_bytes = installment_id_map_auction.get(selected_installment_name_auction)
                                    selected_winner_id_auction_bytes = subscriber_id_map_auction.get(selected_winner_name_auction)

                                    if selected_installment_id_auction_bytes and selected_winner_id_auction_bytes and auction_prize_amount >= 0:
                                         # Call the update function
                                         if update_installment_auction(selected_installment_id_auction_bytes.bytes, auction_prize_amount, selected_winner_id_auction_bytes.bytes): # Pass .bytes
                                              st.rerun() # Rerun to refresh installment list
                                    else:
                                         st.warning("Please select an Installment, Winner, and provide a valid Prize Amount.")
                        else:
                             st.info("No subscribers enrolled in this group yet to select a winner.")

                    else:
                         st.info("All installments for this group have had their auction details recorded.")


                else:
                    st.info(f"No installments found for '{selected_group_name_view_install}'. Generate them above.")
            else:
                st.warning("Could not find the selected group ID.")


elif page == "Record Payments":
    st.header("Record Payments")
    st.write("Record payments made by subscribers for specific installments.")

    # --- Payment Recording Form ---
    # Need to get groups, then installments for group, then subscribers for group
    group_options_payment = get_group_names_and_ids()
    group_display_options_payment = [name for name, id in group_options_payment]
    group_id_map_payment = {name: id for name, id in group_options_payment}

    if not group_display_options_payment:
        st.info("Add a group first to record payments.")
    else:
        # Select Group
        selected_group_name_payment = st.selectbox("Select Group", group_display_options_payment, key="payment_group_select")
        group_id_for_payment_bytes = group_id_map_payment.get(selected_group_name_payment)

        if group_id_for_payment_bytes:
             # Fetch installments for the selected group
             installments_for_payment = get_installments_for_group(group_id_for_payment_bytes)
             if installments_for_payment:
                 # Create options for installment selectbox
                 # Include installment ID in the tuple for mapping back
                 installment_options_payment = [(f"Month {inst['monthNumber']} (Due: {inst['dueDate'].strftime('%Y-%m-%d')})", inst['id']) for inst in installments_for_payment]
                 installment_display_options_payment = [name for name, id in installment_options_payment]
                 installment_id_map_payment = {name: id for name, id in installment_options_payment}

                 # Select Installment
                 selected_installment_name_payment = st.selectbox("Select Installment", installment_display_options_payment, key="payment_install_select")
                 selected_installment_id_payment_uuid = installment_id_map_payment.get(selected_installment_name_payment) # This is a UUID object

                 if selected_installment_id_payment_uuid: # Check if a UUID object was retrieved
                      # Fetch enrolled subscribers for THIS group (Installment is linked to Group)
                      # We need the subscriber ID to record the payment
                      enrolled_subscribers_for_group = get_enrollments_details_for_group(group_id_for_payment_bytes)
                      if enrolled_subscribers_for_group:
                          # Create options for subscriber selectbox
                          # Include subscriber ID in the tuple for mapping back
                          subscriber_options_payment = [(f"{sub['subscriberName']} (Chit No: {sub['assignedChitNumber']})", sub['subscriberId']) for sub in enrolled_subscribers_for_group]
                          subscriber_display_options_payment = [name for name, id in subscriber_options_payment]
                          subscriber_id_map_payment = {name: id for name, id in subscriber_options_payment}

                          # Select Subscriber
                          selected_subscriber_name_payment = st.selectbox("Select Subscriber", subscriber_display_options_payment, key="payment_sub_select")
                          selected_subscriber_id_payment_uuid = subscriber_id_map_payment.get(selected_subscriber_name_payment) # This is a UUID object

                          if selected_subscriber_id_payment_uuid: # Check if a UUID object was retrieved
                              st.markdown("---") # Separator
                              st.subheader("Enter Payment Details")
                              # --- Payment Details Form ---
                              with st.form("record_payment_form"):
                                   amount_paid = st.number_input("Amount Paid", min_value=0.0, format="%.2f", key="payment_amount_input")
                                   notes = st.text_area("Notes (Optional)", key="payment_notes_input")

                                   record_button = st.form_submit_button("Record Payment")

                                   if record_button:
                                       if amount_paid > 0:
                                           # Call the database function to insert the payment
                                           # Pass the .bytes representation of the UUIDs
                                           insert_payment(selected_installment_id_payment_uuid.bytes, selected_subscriber_id_payment_uuid.bytes, amount_paid, notes) # <<< FIX HERE
                                       else:
                                           st.warning("Amount Paid must be greater than zero.")
                          else:
                              st.warning("Could not find the selected subscriber ID.")

                      else:
                           st.info("No subscribers enrolled in this group yet.")

                 else:
                      st.info(f"No installments found for '{selected_group_name_payment}'. Generate them in 'Manage Installments'.")
             else:
                  st.warning("Could not find the selected group ID.")

        st.markdown("---") # Separator

        # --- View Payments for Selected Installment (Optional) ---
        # Add a section to view payments already recorded for the selected installment
        # Check if selected_installment_id_payment_uuid exists and is a UUID object before accessing .bytes
        if 'selected_installment_id_payment_uuid' in locals() and isinstance(selected_installment_id_payment_uuid, uuid.UUID):
             st.subheader("Payments Recorded for Selected Installment")
             # Pass the .bytes representation to the function
             payments_for_selected_install = get_payments_for_installment(selected_installment_id_payment_uuid.bytes) # <<< FIX HERE
             if payments_for_selected_install:
                  st.dataframe(
                       payments_for_selected_install,
                       use_container_width=True,
                       column_config={
                           "paymentId": None, # Hide internal ID
                           "subscriberName": "Paid By",
                           "paymentDate": st.column_config.DatetimeColumn("Payment Date", format="YYYY-MM-DD HH:mm"),
                           "amountPaid": st.column_config.NumberColumn("Amount Paid", format="₹%.2f"),
                           "notes": "Notes"
                       }
                  )
             else:
                  st.info("No payments recorded yet for this installment.")
        # Added an else clause for clarity if the variable isn't set or isn't a UUID
        elif 'selected_installment_id_payment_uuid' in locals() and selected_installment_id_payment_uuid is None:
             st.info("Select an installment above to view recorded payments.")
        # No need for an else if the variable simply doesn't exist yet (e.g., first load)


elif page == "View Dues & Status":
    st.header("View Dues & Status")
    st.write("See the payment status for installments and identify defaulters.")

    # --- Payment Status by Installment ---
    st.subheader("Payment Status by Installment")
    group_options_dues = get_group_names_and_ids()
    group_display_options_dues = [name for name, id in group_options_dues]
    group_id_map_dues = {name: id for name, id in group_options_dues}

    if not group_display_options_dues:
         st.info("Add a group first to check dues.")
    else:
         # Select Group
         selected_group_name_dues = st.selectbox("Select Group", group_display_options_dues, key="dues_group_select")
         group_id_for_dues_bytes = group_id_map_dues.get(selected_group_name_dues)

         if group_id_for_dues_bytes:
             # Fetch installments for the selected group to populate the installment selectbox
             installments_for_dues = get_installments_for_group(group_id_for_dues_bytes)
             if installments_for_dues:
                  # Create options for installment selectbox
                  # Use month number as value for simplicity in the status function
                  installment_options_dues = [(f"Month {inst['monthNumber']} (Due: {inst['dueDate'].strftime('%Y-%m-%d')})", inst['monthNumber']) for inst in installments_for_dues]
                  installment_display_options_dues = [name for name, month_num in installment_options_dues]
                  installment_month_map_dues = {name: month_num for name, month_num in installment_options_dues}

                  # Select Installment Month
                  selected_installment_name_dues = st.selectbox("Select Installment Month", installment_display_options_dues, key="dues_install_select")
                  view_dues_button = st.button("Show Payment Status", key="show_dues_button")

                  if view_dues_button and selected_installment_name_dues:
                      # Get the selected installment month number
                      selected_installment_month_dues = installment_month_map_dues.get(selected_installment_name_dues)

                      if selected_installment_month_dues is not None: # Check if month number was retrieved
                          # Call the dues status function
                          status_list = get_payment_status_for_installment(group_id_for_dues_bytes, selected_installment_month_dues)
                          if status_list:
                              st.subheader(f"Payment Status for {selected_group_name_dues} - Month {selected_installment_month_dues}")
                              # Display the status in a dataframe
                              st.dataframe(
                                  status_list,
                                  use_container_width=True,
                                  column_config={
                                      "Subscriber Name": "Subscriber",
                                      "Chit Number": "Chit No.",
                                      "Status": "Payment Status",
                                      "Total Paid (This Installment)": st.column_config.NumberColumn("Total Paid (This Month)", format="₹%.2f"),
                                      # TODO: Add column configs for 'Expected Amount' and 'Balance Due' once implemented
                                  }
                              )
                          else:
                              st.info(f"No payment status found for Month {selected_installment_month_dues}.")
                      else:
                           st.warning("Could not retrieve the selected installment month.")

             else:
                  st.info(f"No installments found for '{selected_group_name_dues}'. Generate them in 'Manage Installments'.")
         else:
              st.warning("Could not find the selected group ID.")

