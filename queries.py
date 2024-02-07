import pymysql
import pandas as pd
import streamlit as st

DATABASE_CREDENTIALS = {
    "HOST": st.secrets["DB_HOST"],
    "DATABASE": st.secrets["DB_DATABASE"],
    "USER": st.secrets["DB_USER"],
    "PASSWORD": st.secrets["DB_PASSWORD"]
}

class Queries():

    def __init__(self):
        
        self.conn = pymysql.connect(
             host=DATABASE_CREDENTIALS["HOST"],
             user=DATABASE_CREDENTIALS["USER"],    
             password=DATABASE_CREDENTIALS["PASSWORD"], 
             database=DATABASE_CREDENTIALS["DATABASE"],  
         )

    def get_cup_current_info(self, cup_id):

        self.cursor = self.conn.cursor()

        query = f"select cup_status_id, last_cup_event_type_id, current_device_id from cup where id = '{cup_id}'"
        self.cursor.execute(query)
        res = [tuple(row) for row in self.cursor.fetchall()]
        column_names = [column[0] for column in self.cursor.description]
        

        # check if cup has been used before: (if not we have to simulate)
        #caused by an error (first time cup in dispenser and it left wihtout being read)
        if res[0][0] is None:
            res = [(2,3, None)]
            # 2: status user, 3: event left dispenser

        info_df = pd.DataFrame(res, columns=column_names)

        self.cursor.close()

        return info_df["cup_status_id"], info_df["last_cup_event_type_id"], info_df["current_device_id"]

    def get_cup_id(self, cup_name):

        self.cursor = self.conn.cursor()

        query = f"select id from cup where id_name = '{cup_name}'"
        self.cursor.execute(query)
        # et value
        res = [tuple(row) for row in self.cursor.fetchall()]
        self.cursor.close()
        cup_id = res[0][0]
        
        return cup_id

    def register_cups(self, dirty, clean, event_time):
        for cup in dirty:
            cup_id = self.get_cup_id(cup)
            status, last_event, current_device = self.get_cup_current_info(cup_id)
            refund_card_id = self.get_corresponding_refund_card(cup_id, event_time)
            if status[0] != 3: # not in bin
                self.insert_cup_event(cup_id, event_time, refund_card_id)
        for cup in clean:
            cup_id = self.get_cup_id(cup)
            status, last_event, current_device = self.get_cup_current_info(cup_id)
            refund_card_id = self.get_corresponding_refund_card(cup_id, event_time)
            if status[0] != 3: # not in bin
                self.insert_cup_event(cup_id, event_time, refund_card_id, fake=1)
            else: # if in bin
                try:
                    self._decrease_card_returned_cups(refund_card_id)
                except:
                    #only works if card is registered
                    pass
                # turn last event to fake
                self._turn_last_event_to_fake(cup_id)

    def add_dispenser_cups(self, n_cups, event_time, reset_stock = False):

        self.cursor = self.conn.cursor()

        if reset_stock:
            query = f"UPDATE device SET capacity = '{n_cups}', updated_at = '{event_time}' WHERE id = 1;"
        else:
            query = f"UPDATE device SET capacity = capacity + '{n_cups}', updated_at = '{event_time}' WHERE id = 1;"

        self.cursor.execute(query)

        self.conn.commit()
        self.cursor.close()


    # From loopack-prototype
    def insert_cup_event(self, cup_id, event_time, refund_card_id, fake = 0):

        self.cursor = self.conn.cursor()

        current_device_id = 999 # Test bin (unkown)
        cup_event_type_id = 2 # entered colector
        cup_status_id = 3 # in bin

        query = f"UPDATE cup SET cup_status_id = {cup_status_id}, last_cup_event_type_id = {cup_event_type_id}, current_device_id = {current_device_id}, updated_at = '{event_time}' WHERE id = '{cup_id}'"
        self.cursor.execute(query)

        # create new event (set to fake if fake)
        query = f"INSERT INTO cup_event (cup_id, event_time, cup_event_type_id, device_id, refund_card_id, fake) VALUES ('{cup_id}', '{event_time}', {cup_event_type_id}, {current_device_id}, '{refund_card_id}', '{fake}')"
        self.cursor.execute(query)

        self.conn.commit()
        self.cursor.close()
        """ 
        if cup_event_type_id == CupEventType.LEFT_DISPENSER.value:
            self._increase_cup_cycle(cup_id)
        """

        if fake:
            # set last dispenser to fake
            self.cursor = self.conn.cursor()
            query = f"WITH grouped AS (SELECT MAX(event_time) as max_event_time FROM cup_event WHERE cup_event_type_id = 3 GROUP BY cup_id) UPDATE cup_event SET fake = 1 WHERE cup_id = '{cup_id}' and event_time IN (select max_event_time from grouped);"
            # cup_event_id = 3 is left dispenser
            self.cursor.execute(query)
            self.conn.commit()
            self.cursor.close()
        else:
            self._increase_card_returned_cups(refund_card_id)
            self._check_card_returned_cups(refund_card_id)


        if refund_card_id in ["NULL", -999]:
            refund_card_id = None

        return refund_card_id
    
    def _increase_card_returned_cups(self, card_id):

        self.cursor = self.conn.cursor()

        query = f"UPDATE card SET returned_cups = returned_cups + 1 WHERE id = '{card_id}';"

        self.cursor.execute(query)

        self.conn.commit()
        self.cursor.close()

    def _decrease_card_returned_cups(self, card_id):

        self.cursor = self.conn.cursor()

        query = f"UPDATE card SET returned_cups = returned_cups - 1 WHERE id = '{card_id}';"

        self.cursor.execute(query)

        self.conn.commit()
        self.cursor.close()

    def _turn_last_event_to_fake(self, cup_id):
        
        # turn dispenser event to fake
        self.cursor = self.conn.cursor()
        query = f"WITH grouped AS (SELECT MAX(event_time) as max_event_time FROM cup_event WHERE cup_event_type_id = 3 GROUP BY cup_id) UPDATE cup_event SET fake = 1 WHERE cup_id = '{cup_id}' and event_time IN (select max_event_time from grouped);"
        # cup_event_id = 3 is left dispenser
        self.cursor.execute(query)


        # turn bin event to fake
        query = f"WITH grouped AS (SELECT MAX(event_time) as max_event_time FROM cup_event WHERE cup_event_type_id = 2 GROUP BY cup_id) UPDATE cup_event SET fake = 1 WHERE cup_id = '{cup_id}' and event_time IN (select max_event_time from grouped);"
        # cup_event_id = 2 is entered bin
        self.cursor.execute(query)

        self.conn.commit()
        self.cursor.close()

    def _check_card_returned_cups(self, card_id):

        self.cursor = self.conn.cursor()

        query = f"select returned_cups from card where id = '{card_id}'"

        self.cursor.execute(query)
        res = self.cursor.fetchone()

        try:
            num_returned_cups = int(res[0])
        except:
            num_returned_cups = 0

        self.cursor.close()

        if num_returned_cups % 10:
            # EXECUTE THE PROCESS TO ADD CREDIT TO THE LUOPE CARD
            pass

    def get_corresponding_refund_card(self, cup_id, event_time):

        self.cursor = self.conn.cursor()

        refund_card_id = self.__get_refund_card_id(cup_id, event_time)
        if refund_card_id is None:
            refund_card_id = -999
        self.conn.commit()
        self.cursor.close()
        return refund_card_id
    
    def __get_refund_card_id(self, cup_id, event_time):

        self.cursor = self.conn.cursor()

        query = f"select cup_id, event_time, cup_event_type_id, refund_card_id from cup_event where cup_id = '{cup_id}' and event_time <= '{event_time}' order by event_time desc limit 1"
        self.cursor.execute(query)
        res = [tuple(row) for row in self.cursor.fetchall()]
        
        # if couldnt find (no event of left dispenser)
        if len(res) == 0:
            refund_card_id = -999
        else:
            column_names = [column[0] for column in self.cursor.description]
        
            df = pd.DataFrame(res, columns=column_names)
            refund_card_id =  df.iloc[0]["refund_card_id"]
        
        """
        if len(df) == 0:
            print("[MAIN ERROR] No previous data found for this cup.")
            return
        elif df.iloc[0]["cup_event_type_id"] != 3:
            print(f"[MAIN ERROR] Last cup event is not the expected (leave dispenser):\n{df.iloc[0]}")
            return
        """

        return
