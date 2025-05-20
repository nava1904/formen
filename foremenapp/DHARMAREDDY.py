#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 15 00:59:06 2025

@author: navadeepreddy
"""

import streamlit as st
import pandas as pd
import mysql.connector
import toml
from datetime import datetime
def calculate_installment(chit_value, duration):
    """Calculates the installment amount for a chit fund.

    Args:
        chit_value (float): The total value of the chit fund.
        duration (int): The duration of the chit fund in months.

    Returns:
        float: The monthly installment amount. Returns 0 if the duration is not positive.
    """
    if duration > 0:
        return chit_value / duration
    return 0

def calculate_dividend(chit_value, winning_bid_discount_percentage, foreman_commission_percentage, num_members):
    """Calculates the dividend amount per member (excluding the winner).

    Args:
        chit_value (float): The total value of the chit fund.
        winning_bid_discount_percentage (float): The discount percentage at which the auction was won.
        foreman_commission_percentage (float): The foreman's commission percentage.
        num_members (int): The total number of members in the chit fund.

    Returns:
        float: The dividend amount per member. Returns 0 if there's only one member.
    """
    discount_amount = chit_value * (winning_bid_discount_percentage / 100)
    foreman_commission = chit_value * (foreman_commission_percentage / 100)
    if num_members > 1:
        return (discount_amount - foreman_commission) / (num_members - 1)
    return 0

# --- Database Connection ---
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",     # Get host from secrets
            database="DHARMAREDDY", # Get database name from secrets
            user="root",     # Get user from secrets
            password="Vnr@2003"
        )
        if conn.is_connected():
            print(f"Successfully connected to MySQL database: [database]")
            return conn
    except mysql.connector.Error as err:
        print(f"Error: '{err}'")
        return None # Return None if connection fails
    

# --- Database Interaction Functions ---
def fetch_data(conn, query, params=None):
    if conn and conn.is_connected(): # Check if connection is valid
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()
            return results
        except mysql.connector.Error as err:
            print(f"Error executing query: '{err}'")
            return []
    else:
        print("Error: MySQL Connection not available in fetch_data.")
        return []

def execute_query(conn, query, params=None):
    if conn and conn.is_connected(): # Check if connection is valid
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            cursor.close()
            return True
        except mysql.connector.Error as err:
            print(f"Error executing query: '{err}'")
            return False
    else:
        print("Error: MySQL Connection not available in execute_query.")
        return False

# --- Streamlit App ---

# --- Streamlit App ---
st.title("DHARMAREDDY CHIT FUNDS")

conn = get_db_connection() # Establish the connection

if conn: # Only proceed if the connection was successful
    with st.sidebar:
        st.header("Navigation")
        choice = st.sidebar.selectbox("Go to", ("Dashboard", "Members", "Auctions", "Finance", "Reports"))

    if choice == "Dashboard":
        st.subheader("Recent Payments")
        recent_payments_query = """
            SELECT con.payment_date, m.name AS member_name, c.chit_id, con.amount_paid
            FROM Contributions con
            JOIN Members m ON con.member_id = m.member_id
            JOIN Chits c ON con.chit_id = c.chit_id
            ORDER BY con.payment_date DESC
            LIMIT 5
        """
        recent_payments = pd.DataFrame(fetch_data(conn, recent_payments_query))
        if not recent_payments.empty:
            st.dataframe(recent_payments)
        else:
            st.info("No recent payment data available.")


conn = get_db_connection()

if conn:
    # --- Sidebar for Navigation ---
    st.sidebar.header("Navigation")
    menu = ["Dashboard","Chit Setup","Members","Auctions","Finance","Reports"]
    choice = st.sidebar.selectbox("Go to", menu)

    # --- Dashboard ---
    if choice == "Dashboard":
        st.header("Dashboard")

        # Payment Reports
        st.subheader("Recent Payments")
        recent_payments_query = """
            SELECT con.payment_date, m.name AS member_name, c.chit_id, con.amount_paid
            FROM Contributions con
            JOIN Members m ON con.member_id = m.member_id
            JOIN Chits c ON con.chit_id = c.chit_id
            ORDER BY con.payment_date DESC
            LIMIT 5
        """
        recent_payments = pd.DataFrame(fetch_data(conn, recent_payments_query))
        if not recent_payments.empty:
            st.dataframe(recent_payments)
        else:
            st.info("No payment data available.")

        # Auction Reports
        st.subheader("Recent Auctions")
        recent_auctions_query = """
            SELECT a.auction_date, c.chit_id, m.name AS winner_name, a.prize_money
            FROM Auctions a
            JOIN Chits c ON a.chit_id = c.chit_id
            LEFT JOIN Members m ON a.winner_id = m.member_id
            ORDER BY a.auction_date DESC
            LIMIT 5
        """
        recent_auctions = pd.DataFrame(fetch_data(conn, recent_auctions_query))
        if not recent_auctions.empty:
            st.dataframe(recent_auctions)
        else:
            st.info("No auction data available.")

        # Add more dashboard elements as needed

    # --- Chit Setup ---
    elif choice == "Chit Setup":
        st.header("Setup/Edit Chit Fund")

        # Add New Chit
        with st.expander("Add New Chit Fund"):
            with st.form("new_chit_form"):
                chit_id = st.text_input("Chit ID (Unique Identifier)")
                chit_value = st.number_input("Chit Value (₹)", min_value=1000, step=1000)
                duration = st.number_input("Duration (Months)", min_value=1, step=1)
                foreman_commission = st.number_input("Foreman Commission (%)", min_value=0.0, max_value=7.0, value=5.0)
                start_date = st.date_input("Start Date", min_value=datetime.now().date())
                submitted = st.form_submit_button("Create Chit")
                if submitted:
                    if chit_id and chit_value > 0 and duration > 0:
                        installment = calculate_installment(chit_value, duration)
                        insert_chit_query = "INSERT INTO Chits (chit_id, chit_value, duration, foreman_commission_percentage, start_date, installment_amount) VALUES (%s, %s, %s, %s, %s, %s)"
                        try:
                            execute_query(conn, insert_chit_query, (chit_id, chit_value, duration, foreman_commission, start_date, installment))
                            st.success(f"Chit Fund '{chit_id}' created successfully!")
                        except mysql.connector.Error as e:
                            st.error(f"Error creating chit: {e}")
                    else:
                        st.error("Please fill all the required details for the Chit Fund.")

        # Edit Chit
        with st.expander("Edit Existing Chit Fund"):
            chit_ids = [""] + [row['chit_id'] for row in fetch_data(conn, "SELECT chit_id FROM Chits")]
            selected_chit_id_edit = st.selectbox("Select Chit to Edit", chit_ids)
            if selected_chit_id_edit:
                chit_data_edit_query = "SELECT * FROM Chits WHERE chit_id = %s"
                current_chit_data = fetch_data(conn, chit_data_edit_query, (selected_chit_id_edit,))
                if current_chit_data:
                    current_chit = current_chit_data
                    with st.form(f"edit_chit_form_{selected_chit_id_edit}"):
                        edit_chit_value = st.number_input("Chit Value (₹)", min_value=1000, step=1000, value=current_chit['chit_value'])
                        edit_duration = st.number_input("Duration (Months)", min_value=1, step=1, value=current_chit['duration'])
                        edit_foreman_commission = st.number_input("Foreman Commission (%)", min_value=0.0, max_value=7.0, value=float(current_chit['foreman_commission_percentage']))
                        edit_start_date = st.date_input("Start Date", value=current_chit['start_date'])
                        update_submitted = st.form_submit_button("Save Changes")
                        if update_submitted:
                            update_chit_query = "UPDATE Chits SET chit_value = %s, duration = %s, foreman_commission_percentage = %s, start_date = %s, installment_amount = %s WHERE chit_id = %s"
                            edit_installment = calculate_installment(edit_chit_value, edit_duration)
                            try:
                                execute_query(conn, update_chit_query, (edit_chit_value, edit_duration, edit_foreman_commission, edit_start_date, edit_installment, selected_chit_id_edit))
                                st.success(f"Chit Fund '{selected_chit_id_edit}' updated successfully!")
                            except mysql.connector.Error as e:
                                st.error(f"Error updating chit: {e}")

        # Delete Chit
        with st.expander("Delete Existing Chit Fund"):
            chit_ids_delete = [""] + [row['chit_id'] for row in fetch_data(conn, "SELECT chit_id FROM Chits")]
            selected_chit_id_delete = st.selectbox("Select Chit to Delete", chit_ids_delete)
            if selected_chit_id_delete:
                if st.button(f"Delete Chit Fund '{selected_chit_id_delete}'", key=f"delete_chit_{selected_chit_id_delete}"):
                    delete_chit_query = "DELETE FROM Chits WHERE chit_id = %s"
                    try:
                        execute_query(conn, delete_chit_query, (selected_chit_id_delete,))
                        st.success(f"Chit Fund '{selected_chit_id_delete}' deleted successfully!")
                        st.rerun() # Refresh the app to see the updated list
                    except mysql.connector.Error as e:
                        st.error(f"Error deleting chit: {e}")

        st.subheader("Current Chit Funds")
        chits_df = pd.DataFrame(fetch_data(conn, "SELECT * FROM Chits"))
        st.dataframe(chits_df)

    # --- Members Section ---
    elif choice == "Members":
        st.header("Manage Members")

        # Add new member
        with st.expander("Add New Member"):
            with st.form("add_member_form"):
                name = st.text_input("Name")
                contact = st.text_input("Contact Number")
                chit_id = st.selectbox("Chit Group", [""] + [row['chit_id'] for row in fetch_data(conn, "SELECT chit_id FROM Chits")])
                join_date = st.date_input("Join Date", min_value=datetime.now().date())
                submitted = st.form_submit_button("Add Member")
                if submitted:
                    if name and contact and chit_id:
                        insert_member_query = "INSERT INTO Members (name, contact, chit_id, join_date) VALUES (%s, %s, %s, %s)"
                        try:
                            execute_query(conn, insert_member_query, (name, contact, chit_id, join_date))
                            st.success(f"Member '{name}' added to Chit Group '{chit_id}'")
                        except mysql.connector.Error as e:
                            st.error(f"Error adding member: {e}")
                    else:
                        st.error("Please fill all the member details.")

        # Edit Member
        with st.expander("Edit Existing Member"):
            members_list_edit_query = "SELECT member_id, name FROM Members"
            members_list_edit = {row['member_id']: row['name'] for row in fetch_data(conn, members_list_edit_query)}
            selected_member_id_edit = st.selectbox("Select Member to Edit", [""] + list(members_list_edit.keys()), format_func=lambda x: members_list_edit.get(x) if x else "")
            if selected_member_id_edit:
                member_data_edit_query = "SELECT name, contact, chit_id, join_date FROM Members WHERE member_id = %s"
                current_member_data = fetch_data(conn, member_data_edit_query, (selected_member_id_edit,))
                if current_member_data:
                    current_member = current_member_data
                    with st.form(f"edit_member_form_{selected_member_id_edit}"):
                        edit_name = st.text_input("Name", value=current_member['name'])
                        edit_contact = st.text_input("Contact Number", value=current_member['contact'])
                        edit_chit_id = st.selectbox("Chit Group", [""] + [row['chit_id'] for row in fetch_data(conn, "SELECT chit_id FROM Chits")], index=[i for i, chit in enumerate([""] + [row['chit_id'] for row in fetch_data(conn, "SELECT chit_id FROM Chits")]) if chit == current_member['chit_id']])
                        edit_join_date = st.date_input("Join Date", value=current_member['join_date'])
                        update_submitted = st.form_submit_button("Save Changes")
                        if update_submitted:
                            update_member_query = "UPDATE Members SET name = %s, contact = %s, chit_id = %s, join_date = %s WHERE member_id = %s"
                            try:
                                execute_query(conn, update_member_query, (edit_name, edit_contact, edit_chit_id, edit_join_date, selected_member_id_edit))
                                st.success(f"Member '{edit_name}' updated successfully!")
                            except mysql.connector.Error as e:
                                st.error(f"Error updating member: {e}")

        # Delete Member
        with st.expander("Delete Existing Member"):
            members_list_delete_query = "SELECT member_id, name FROM Members"
            members_list_delete = {row['member_id']: row['name'] for row in fetch_data(conn, members_list_delete_query)}
            selected_member_id_delete = st.selectbox("Select Member to Delete", [""] + list(members_list_delete.keys()), format_func=lambda x: members_list_delete.get(x) if x else "")
            if selected_member_id_delete:
                if st.button(f"Delete Member '{members_list_delete.get(selected_member_id_delete)}'", key=f"delete_member_{selected_member_id_delete}"):
                    delete_member_query = "DELETE FROM Members WHERE member_id = %s"
                    try:
                        execute_query(conn, delete_member_query, (selected_member_id_delete,))
                        st.success(f"Member '{members_list_delete.get(selected_member_id_delete)}' deleted successfully!")
                        st.rerun()
                    except mysql.connector.Error as e:
                        st.error(f"Error deleting member: {e}")

        st.subheader("Member List")
        members_df = pd.DataFrame(fetch_data(conn, "SELECT m.member_id, m.name, m.contact, m.chit_id, m.join_date, c.chit_value FROM Members m JOIN Chits c ON m.chit_id = c.chit_id"))
        st.dataframe(members_df)

        # Filter members by Chit Group
        chit_groups = ["All"] + [row['chit_id'] for row in fetch_data(conn, "SELECT chit_id FROM Chits")]
        selected_chit_group = st.selectbox("Filter by Chit Group", chit_groups)
        if selected_chit_group!= "All":
            filtered_members = members_df[members_df['chit_id'] == selected_chit_group]
            st.subheader(f"Members in Chit Group '{selected_chit_group}'")
            st.dataframe(filtered_members)

    # --- Auctions Section ---
    elif choice == "Auctions":
        st.header("Manage Auctions")

        # Schedule new auction
        with st.expander("Schedule New Auction"):
            with st.form("schedule_auction_form"):
                chit_id = st.selectbox("Chit Group", [""] + [row['chit_id'] for row in fetch_data(conn, "SELECT chit_id FROM Chits")])
                auction_date = st.date_input("Auction Date", min_value=datetime.now().date())
                submitted = st.form_submit_button("Schedule Auction")
                if submitted:
                    if chit_id:
                        insert_auction_query = "INSERT INTO Auctions (chit_id, auction_date) VALUES (%s, %s)"
                        try:
                            execute_query(conn, insert_auction_query, (chit_id, auction_date))
                            st.success(f"Auction scheduled for Chit Group '{chit_id}' on {auction_date}")
                        except mysql.connector.Error as e:
                            st.error(f"Error scheduling auction: {e}")
                    else:
                        st.error("Please select a Chit Group.")

        # Edit Auction
        with st.expander("Edit Existing Auction"):
            auctions_list_edit_query = "SELECT auction_id, chit_id, auction_date FROM Auctions ORDER BY auction_date DESC"
            auctions_list_edit = {(row['auction_id'], row['chit_id'], row['auction_date']): f"Chit: {row['chit_id']}, Date: {row['auction_date']}" for row in fetch_data(conn, auctions_list_edit_query)}
            selected_auction_tuple_edit = st.selectbox("Select Auction to Edit", [""] + list(auctions_list_edit.keys()), format_func=lambda x: auctions_list_edit.get(x) if x else "")
            if selected_auction_tuple_edit:
                auction_id_edit, chit_id_edit, auction_date_edit = selected_auction_tuple_edit
                auction_data_edit_query = "SELECT winner_id, winning_bid_discount_percentage, prize_money FROM Auctions WHERE auction_id = %s"
                current_auction_data = fetch_data(conn, auction_data_edit_query, (auction_id_edit,))
                if current_auction_data:
                    current_auction = current_auction_data
                    members_in_chit_query = "SELECT member_id, name FROM Members WHERE chit_id = %s"
                    members_in_chit = {row['member_id']: row['name'] for row in fetch_data(conn, members_in_chit_query, (chit_id_edit,)) if chit_id_edit}
                    with st.form(f"edit_auction_form_{auction_id_edit}"):
                        edit_winner_id = st.selectbox("Winner Member", [""] + list(members_in_chit.keys()), format_func=lambda x: members_in_chit.get(x) if x else "", index=[i for i, member_id in enumerate([""] + list(members_in_chit.keys())) if member_id == current_auction['winner_id']] if current_auction['winner_id'] else 0)
                        edit_winning_bid_discount = st.number_input("Winning Bid Discount (%)", min_value=0.0, max_value=40.0, step=0.5, value=float(current_auction['winning_bid_discount_percentage']) if current_auction['winning_bid_discount_percentage'] else 0.0)
                        edit_prize_money = st.number_input("Prize Money (₹)", min_value=0.0, step=100, value=float(current_auction['prize_money']) if current_auction['prize_money'] is not None else 0.0)
                        update_submitted = st.form_submit_button("Save Changes")
                        if update_submitted:
                            update_auction_query = "UPDATE Auctions SET winner_id = %s, winning_bid_discount_percentage = %s, prize_money = %s WHERE auction_id = %s"
                            try:
                                execute_query(conn, update_auction_query, (edit_winner_id, edit_winning_bid_discount, edit_prize_money, auction_id_edit))
                                st.success(f"Auction for Chit '{chit_id_edit}' on {auction_date_edit} updated successfully!")
                            except mysql.connector.Error as e:
                                st.error(f"Error updating auction: {e}")

        # Delete Auction
        with st.expander("Delete Existing Auction"):
            auctions_list_delete_query = "SELECT auction_id, chit_id, auction_date FROM Auctions ORDER BY auction_date DESC"
            auctions_list_delete = {(row['auction_id'], row['chit_id'], row['auction_date']): f"Chit: {row['chit_id']}, Date: {row['auction_date']}" for row in fetch_data(conn, auctions_list_delete_query)}
            selected_auction_tuple_delete = st.selectbox("Select Auction to Delete", [""] + list(auctions_list_delete.keys()), format_func=lambda x: auctions_list_delete.get(x) if x else "")
            if selected_auction_tuple_delete:
                auction_id_delete, chit_id_delete, auction_date_delete = selected_auction_tuple_delete
                if st.button(f"Delete Auction for Chit '{chit_id_delete}' on {auction_date_delete}", key=f"delete_auction_{auction_id_delete}"):
                    delete_auction_query = "DELETE FROM Auctions WHERE auction_id = %s"
                    try:
                        execute_query(conn, delete_auction_query, (auction_id_delete,))
                        st.success(f"Auction for Chit '{chit_id_delete}' on {auction_date_delete} deleted successfully!")
                        st.rerun()
                    except mysql.connector.Error as e:
                        st.error(f"Error deleting auction: {e}")

        st.subheader("Upcoming Auctions")
        upcoming_auctions_query = "SELECT a.auction_id, c.chit_id, a.auction_date FROM Auctions a JOIN Chits c ON a.chit_id = c.chit_id WHERE a.auction_date >= CURDATE() ORDER BY a.auction_date"
        upcoming_auctions = pd.DataFrame(fetch_data(conn, upcoming_auctions_query))
        st.dataframe(upcoming_auctions)

        st.subheader("Past Auctions")
        past_auctions_query = "SELECT a.auction_id, c.chit_id, a.auction_date, m.name as winner, a.winning_bid_discount_percentage, a.prize_money FROM Auctions a JOIN Chits c ON a.chit_id = c.chit_id LEFT JOIN Members m ON a.winner_id = m.member_id WHERE a.auction_date < CURDATE() ORDER BY a.auction_date DESC"
        past_auctions = pd.DataFrame(fetch_data(conn, past_auctions_query))
        st.dataframe(past_auctions)

    # --- Finance Section ---
    elif choice == "Finance":
        st.header("Manage Finances")

        # Record Contribution
        with st.expander("Record/Edit Contribution"):
            with st.form("record_contribution_form"):
                members_list_query = "SELECT member_id, name, chit_id FROM Members"
                members_list = {(row['member_id'], row['chit_id']): row['name'] for row in fetch_data(conn, members_list_query)}
                member_chit_tuple = st.selectbox("Member and Chit Group", [""] + list(members_list.keys()), format_func=lambda x: f"{members_list.get(x)} ({x})" if x else "")
                contribution_month = st.number_input("Month Number", min_value=1, step=1)
                amount_paid = st.number_input("Amount Paid (₹)", min_value=1)
                payment_date = st.date_input("Payment Date", min_value=datetime.now().date())
                submitted_contrib = st.form_submit_button("Record Contribution")
                if submitted_contrib and member_chit_tuple:
                    member_id_contrib, chit_id_contrib = member_chit_tuple
                    insert_contribution_query = "INSERT INTO Contributions (member_id, chit_id, month_number, amount_paid, payment_date) VALUES (%s, %s, %s, %s, %s)"
                    try:
                        execute_query(conn, insert_contribution_query, (member_id_contrib, chit_id_contrib, contribution_month, amount_paid, payment_date))
                        st.success("Contribution recorded successfully!")
                    except mysql.connector.Error as e:
                        st.error(f"Error recording contribution: {e}")
                elif submitted_contrib:
                    st.error("Please select a Member and Chit Group.")

            # Edit Contribution
            st.subheader("Edit Contribution")
            contributions_list_query = """
                SELECT con.contribution_id, m.name as member_name, c.chit_id, con.month_number, con.payment_date
                FROM Contributions con
                JOIN Members m ON con.member_id = m.member_id
                JOIN Chits c ON con.chit_id = c.chit_id
                ORDER BY con.payment_date DESC
            """
            contributions_list = {(row['contribution_id'], row['member_name'], row['chit_id'], row['month_number']): f"ID: {row['contribution_id']}, Member: {row['member_name']}, Chit: {row['chit_id']}, Month: {row['month_number']}" for row in fetch_data(conn, contributions_list_query)}
            selected_contribution_tuple_edit = st.selectbox("Select Contribution to Edit", [""] + list(contributions_list.keys()), format_func=lambda x: contributions_list.get(x) if x else "")
            if selected_contribution_tuple_edit:
                contribution_id_edit, member_name_edit, chit_id_edit, month_number_edit = selected_contribution_tuple_edit
                contribution_data_edit_query = "SELECT amount_paid, payment_date FROM Contributions WHERE contribution_id = %s"
                current_contribution_data = fetch_data(conn, contribution_data_edit_query, (contribution_id_edit,))
                if current_contribution_data:
                    current_contribution = current_contribution_data
                    with st.form(f"edit_contribution_form_{contribution_id_edit}"):
                        edit_amount_paid = st.number_input("Amount Paid (₹)", min_value=1, value=float(current_contribution['amount_paid']))
                        edit_payment_date = st.date_input("Payment Date", value=current_contribution['payment_date'])
                        update_submitted = st.form_submit_button("Save Changes")
                        if update_submitted:
                            update_contribution_query = "UPDATE Contributions SET amount_paid = %s, payment_date = %s WHERE contribution_id = %s"
                            try:
                                execute_query(conn, update_contribution_query, (edit_amount_paid, edit_payment_date, contribution_id_edit))
                                st.success(f"Contribution ID '{contribution_id_edit}' updated successfully!")
                            except mysql.connector.Error as e:
                                st.error(f"Error updating contribution: {e}")

            # Delete Contribution
            st.subheader("Delete Contribution")
            selected_contribution_tuple_delete = st.selectbox("Select Contribution to Delete", [""] + list(contributions_list.keys()), format_func=lambda x: contributions_list.get(x) if x else "", key="delete_contribution_select")
            if selected_contribution_tuple_delete:
                contribution_id_delete, member_name_delete, chit_id_delete, month_number_delete = selected_contribution_tuple_delete
                if st.button(f"Delete Contribution ID '{contribution_id_delete}'", key=f"delete_contribution_{contribution_id_delete}"):
                    delete_contribution_query = "DELETE FROM Contributions WHERE contribution_id = %s"
                    try:
                        execute_query(conn, delete_contribution_query, (contribution_id_delete,))
                        st.success(f"Contribution ID '{contribution_id_delete}' deleted successfully!")
                        st.rerun()
                    except mysql.connector.Error as e:
                        st.error(f"Error deleting contribution: {e}")

        st.subheader("Contribution History")
        contributions_df = pd.DataFrame(fetch_data(conn, "SELECT con.contribution_id, m.name as member_name, c.chit_id, con.month_number, con.amount_paid, con.payment_date FROM Contributions con JOIN Members m ON con.member_id = m.member_id JOIN Chits c ON con.chit_id = c.chit_id"))
        st.dataframe(contributions_df)

        # Calculate and Distribute Dividend (unchanged for brevity, can be extended for edit/delete)
        with st.expander("Calculate and Distribute Dividend"):
            with st.form("calculate_dividend_form"):
                chit_id_dividend = st.selectbox("Select Chit Group for Dividend", [""] + [row['chit_id'] for row in fetch_data(conn, "SELECT chit_id FROM Chits")])
                auction_date_dividend = st.date_input("Auction Date", min_value=datetime.now().date())
                submitted_dividend = st.form_submit_button("Calculate and Record Dividend")
                if submitted_dividend and chit_id_dividend:
                    auction_result_query = "SELECT winner_id, winning_bid_discount_percentage FROM Auctions WHERE chit_id = %s AND auction_date = %s"
                    auction_result = fetch_data(conn, auction_result_query, (chit_id_dividend, auction_date_dividend))
                    if auction_result:
                        winner_id_auction = auction_result[winner_id]
                        winning_bid_discount_percentage = auction_result['winning_bid_discount_percentage']

                        chit_details_query = "SELECT chit_value, foreman_commission_percentage, duration FROM Chits WHERE chit_id = %s"
                        chit_details = fetch_data(conn, chit_details_query, (chit_id_dividend,))
                        num_members_query = "SELECT COUNT(*) as count FROM Members WHERE chit_id = %s"
                        num_members = fetch_data(conn, num_members_query, (chit_id_dividend,))['count']

                        if winner_id_auction and winning_bid_discount_percentage is not None and num_members > 1:
                            dividend_amount = calculate_dividend(chit_details[chit_value], winning_bid_discount_percentage, chit_details[foreman_commission_percentage], num_members)
                            members_in_chit_query = "SELECT member_id FROM Members WHERE chit_id = %s"
                            members_in_chit = [row['member_id'] for row in fetch_data(conn, members_in_chit_query, (chit_id_dividend,))]

                            for member_id in members_in_chit:
                                if member_id!= winner_id_auction:
                                    insert_dividend_query = "INSERT INTO Dividends (chit_id, member_id, auction_date, dividend_amount, distribution_date) VALUES (%s, %s, %s, %s, %s)"
                                    try:
                                        execute_query(conn, insert_dividend_query, (chit_id_dividend, member_id, auction_date_dividend, dividend_amount, datetime.now().date()))
                                    except mysql.connector.Error as e:
                                        st.error(f"Error recording dividend: {e}")
                            st.success(f"Dividend calculated and recorded for Chit '{chit_id_dividend}' for the auction on {auction_date_dividend}.")
                        else:
                            st.warning("Could not calculate dividend. Check auction result and number of members.")
                    else:
                        st.warning(f"No auction found for Chit '{chit_id_dividend}' on {auction_date_dividend}.")

        st.subheader("Dividend History")
        dividends_df = pd.DataFrame(fetch_data(conn, "SELECT div.dividend_id, m.name as member_name, c.chit_id, div.auction_date, div.dividend_amount, div.distribution_date FROM Dividends div JOIN Members m ON div.member_id = m.member_id JOIN Chits c ON div.chit_id = c.chit_id"))
        st.dataframe(dividends_df)

    # --- Reports Section ---
    elif choice == "Reports":
        st.header("Generate Reports")

        report_queries = {
            "Chit Funds": "SELECT * FROM Chits",
            "Members": "SELECT m.member_id, m.name, m.contact, m.chit_id, m.join_date, c.chit_value FROM Members m JOIN Chits c ON m.chit_id = c.chit_id",
            "Auction History": "SELECT a.auction_id, c.chit_id, a.auction_date, m.name as winner, a.winning_bid_discount_percentage, a.prize_money FROM Auctions a JOIN Chits c ON a.chit_id = c.chit_id LEFT JOIN Members m ON a.winner_id = m.member_id",
            "Contribution History": "SELECT con.contribution_id, m.name as member_name, c.chit_id, con.month_number, con.amount_paid, con.payment_date FROM Contributions con JOIN Members m ON con.member_id = m.member_id JOIN Chits c ON con.chit_id = c.chit_id",
            "Dividend History": "SELECT div.dividend_id, m.name as member_name, c.chit_id, div.auction_date, div.dividend_amount, div.distribution_date FROM Dividends div JOIN Members m ON div.member_id = m.member_id JOIN Chits c ON div.chit_id = c.chit_id"
        }

        for report_name, query in report_queries.items():
            st.subheader(report_name)
            df = pd.DataFrame(fetch_data(conn, query))
            st.dataframe(df)
            if not df.empty:
                st.download_button(
                    label=f"Download {report_name} (CSV)",
                    data=df.to_csv(index=False).encode('utf-8'),
                    file_name=f"{report_name.lower()}.csv",
                    mime='text/csv',
                )

    conn.close()
else:
    st.error("Could not connect to the database. Please check your credentials in Streamlit secrets.")
