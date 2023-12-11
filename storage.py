import sqlite3
import pandas as pd
DBNAME = "webapp_database.db"

class Collection:
    """
    Collection class acts as an interface with the database and its tables.

    Parameters:
    tblname

    Methods:
    _execute(query, values=None)
    _return(query, values=None, multi=False)
    _is_exist(tblname, left_key, left_value, right_key=None, right_value=None)
    _display(row_list)
    _retrieve_id(tblname, name, name_key, id_key, like=False)
    display_all()
    """
    def __init__(self, tblname):
        self._dbname = DBNAME
        self._tblname = tblname

    def __repr__(self):
        return f'Collection({self.tblname})'

    def _execute(self, query, values=None):
        conn = sqlite3.connect(self._dbname)
        c = conn.cursor()
        if values is None:
            c.execute(query)
        else:
            c.execute(query, values)
        conn.commit()
        conn.close()

    def _return(self, query, values=None, multi=False):
        conn = sqlite3.connect(self._dbname)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        if values is None:
            c.execute(query)
        else:
            c.execute(query, values)
        if multi:
            row = c.fetchall()
        else:
            row = c.fetchone()
        conn.close()
        return row # sqlite3.Row object (supports both numerical and key indexing)

    def _is_exist(self, tblname, left_key, left_value, right_key=None, right_value=None):
        """Checks whether a record exists in a table.
        Supports composite keys for junction tables
        """
        if right_key is not None:
            query = f"""
                    SELECT *
                    FROM '{tblname}'
                    WHERE '{tblname}'.'{left_key}' = ?
                    AND '{tblname}'.'{right_key}' = ?;
                    """
            row = self._return(query, (left_value, right_value,))
        else:
            query = f"""
                    SELECT *
                    FROM '{tblname}'
                    WHERE '{tblname}'.'{left_key}' = ?;
                    """
            row = self._return(query, (left_value,))

        if row is None:
            return False
        return True

    def _display(self, row_list):
        headers = row_list[0].keys()
        tables = []
        for row in row_list:
            tables.append([row[i] for i in range(len(row))])
        df = pd.DataFrame(tables, columns = headers)
        print(df)

    def _retrieve_id(self, tblname, name, name_key, id_key, like=False):
        """Retrieves id linked to name; return False if name
        does not exist in tblname

        E.g. _retrieve_id(tblname='Students', name='Moses', name_key='student_name', 
        id_key='student_id')
        """

        # retrieve student_id
        if like:
            query = f"""
                SELECT {id_key}
                FROM {tblname}
                WHERE {name_key} LIKE ?;
                """
            values = ('%'+name+'%',)
        else:
            query = f"""
                    SELECT {id_key}
                    FROM {tblname}
                    WHERE {name_key} = ?;
                    """
            values = (name,)
        row = self._return(query, values, multi=False)
        #check if name exists
        if row is None:
            return False
        name_id = row[id_key]
        return name_id

    def display_all(self):
        """Display all the records in a collection"""
        query = f"""SELECT * FROM '{self._tblname}'"""
        rows = self._return(query, multi=True)
        self._display(rows)
        

class Students(Collection):
    """
    Student Collection
    Methods:
    --------
    add(record)
    get(student_name)
    update(student_name, record)
    delete(student_name)
    """
    def __init__(self):
        super().__init__("Students")

    def add(self, record):
        """Adds a student record into the database."""
        # check if student exists
        if self._is_exist(self._tblname, "student_name", record["student_name"]):
            return False
        
        class_id = self._retrieve_id('Classes', record['class_name'], 'class_name', 'class_id')
        if not class_id:
            return False
        record["class_id"] = class_id
        
        # add student record
        query = f"""
                INSERT INTO '{self._tblname}' (
                    'student_name', 'age', 'year_enrolled', 'grad_year', 'class_id'
                ) VALUES (:student_name, :age, :year_enrolled, :grad_year, :class_id);
                """
        self._execute(query, record)
        return
        
    def get(self, student_name):
        """Returns a student's record."""
        #retrieve student record
        query = f"""
                SELECT
                    'Students'.'student_name',
                    'Students'.'age',
                    'Students'.'year_enrolled',
                    'Students'.'grad_year',
                    'Classes'.'class_name',
                    'Students'.'student_id'
                FROM '{self._tblname}'
                INNER JOIN 'Classes'
                ON 'Students'.'class_id' = 'Classes'.'class_id'
                WHERE student_name LIKE ?;
                """
        values = ('%' + student_name + '%',)
        row = self._return(query, values, multi=False)

        # check if student exists
        if row is None:
            return False
        
        data = {}
        data["student_name"] = row['student_name']
        data["age"] = row["age"]
        data["year_enrolled"] = row["year_enrolled"]
        data["grad_year"] = row["grad_year"]
        data['class_name'] = row["class_name"]
        data['student_id'] = row['student_id']

        return data

    def update(self, student_name, record):
        """Updates student record in database."""
        # check if student exists
        if not self._is_exist(self._tblname, "student_name", student_name):
            return False

        # retrieve class_id
        class_id = self._retrieve_id('Classes', record['new_class_name'], 'class_name', 'class_id')
        if not class_id:
            return False
        
        # update student record
        query = f"""
                UPDATE '{self._tblname}' SET
                    'student_name' = ?,
                    'age' = ?,
                    'year_enrolled' = ?,
                    'grad_year' = ?,
                    'class_id' = ?
                WHERE student_name = ?;
                """
        values = (record["new_student_name"], record["new_age"], record["new_year_enrolled"], record["new_grad_year"], class_id, student_name,)
        self._execute(query, values)
        return
        
    def delete(self, student_name):
        """Deletes student record from database."""
        # retrieve student_id
        student_id = self._retrieve_id('Students', student_name, 'student_name', 'student_id')
        if not student_id:
            return False
        
        # delete from Students-Activities, Students-CCAs, Students-Subjects and Students table
        tblnames = ["Students-Activities", "Students-CCAs", "Students-Subjects", "Students"]
        for tblname in tblnames:
            query = f"""
                    DELETE FROM '{tblname}'
                    WHERE student_id = ?;
                    """
            values = (student_id,)
            self._execute(query, values)
        return


class Classes(Collection):
    """
    Classes Collection
    
    Methods:
    --------
    add(record)
    get(class_name)
    get_info(class_name)
    update(class_name, record)
    """
    def __init__(self):
        super().__init__("Classes")

    def add(self, record):
        """Adds a class record to the database."""
        # check if class exists
        if self._is_exist(self._tblname, "class_name", record["class_name"]):
            return False

        # add class record
        query = f"""
                INSERT INTO '{self._tblname}' (
                    'class_name', 'level'
                ) VALUES (:class_name, :level);
                """
        self._execute(query, record)
        return

    def get_info(self, class_name):
        """Returns the class info"""
        # retrieve Class record
        query = """
                SELECT *
                FROM 'Classes'
                WHERE class_name LIKE ?;
                """
        values = ('%'+class_name+'%',)
        row = self._return(query, values, multi=False)
        if row is None:
            return False
        
        # convert data to dictionary
        field_names = row.keys()
        data = {}
        for i, elem in enumerate(field_names):
            data[elem] = row[i]
        return data

    def get(self, class_name):
        """Returns all students in the corresponding class."""
        # retrieve student_id and student_name
        query = """
                SELECT 
                    'Students'.'student_id',
                    'Students'.'student_name'
                FROM 'Students'
                INNER JOIN 'Classes'
                ON 'Students'.'class_id' = 'Classes'.'class_id'
                WHERE 'Classes'.'class_name' LIKE ?
                ORDER BY 'student_id' ASC;
                """
        values = ('%'+class_name+'%',)
        row = self._return(query, values, multi=True)
        if row == []:
            return False

        # convert data to dictionary (key=id, value=student_name)
        data = []
        for item in row:
            record = {}
            record['student_id'] = item['student_id']
            record['student_name'] = item["student_name"]
            data.append(record)
        return data

    def update(self, class_name, record):
        """Updates class record in the database."""
        # check if class exists
        if not self._is_exist(self._tblname, "class_name", class_name):
            return False

        # update class record
        query = f"""
                UPDATE '{self._tblname}' SET
                    'class_name' = ?,
                    'level' = ?
                WHERE class_name = ?;
                """
        values = (record["new_class_name"], record["new_level"], class_name,)
        self._execute(query, values)
        return


class Subjects(Collection):
    """
    Subjects Collection

    Methods:
    --------
    _subj_is_exist(subj_list)
    add_student(record)
    get_student(student_name)
    delete_student(record)
    """
    def __init__(self):
        super().__init__("Subjects")

    def _subj_is_exist(self, subj_list):
        """Returns a list of subj_id for each subj in subj_list
        if every subj in subj_list exist in Subjects table, else return False"""
        subj_id_list = []
        for subj in subj_list:
            query = f"""
                    SELECT *
                    FROM '{self._tblname}'
                    WHERE subj_name = ?
                    AND level = ?;
                    """
            values = tuple(subj.values())
            row = self._return(query, values, multi=False)
            if row is None:
                return False
            subj_id_list.append(row["subj_id"])
        return subj_id_list

    def add_student(self, record):
        """Adds a student's subjects.
        record = {'student_name': ...,
                  'subj_list': [{'subj_name': ..., 'level': ...}, ...]}
        Returns False if student does not exist or subj does not exist
        """
        # check if each subject exists and retrieve subject_id
        subj_list = record["subj_list"]
        subj_id_list = self._subj_is_exist(subj_list)
        if not subj_id_list:
            return False

        # retrieve student_id
        student_id = self._retrieve_id('Students', record['student_name'], 'student_name', 'student_id', like=True)
        if not student_id:
            return False
            
        # add each student-subject record
        for subj_id in subj_id_list:
            record = {}
            record["student_id"] = student_id
            record["subj_id"] = subj_id
            query = """
                    INSERT INTO 'Students-Subjects' (
                        'student_id', 'subj_id'
                    ) VALUES (:student_id, :subj_id);
                    """
            self._execute(query, record)
        return

    def get_student(self, student_name):
        """Returns a list of subj that student takes"""
        #retrieve the subj_id for subj that student takes
        query = """
                SELECT * 
                FROM 'Students-Subjects'
                INNER JOIN 'Subjects'
                ON 'Students-Subjects'.'subj_id' = 'Subjects'.'subj_id'
                INNER JOIN 'Students'
                ON 'Students'.'student_id' = 'Students-Subjects'.'student_id'
                WHERE student_name LIKE ?;
                """
        values = ('%'+student_name+'%',)
        subj_list = self._return(query, values, multi=True)
        if subj_list == []:
            return False
        data = []
        for subj in subj_list:
            data.append({'subj_name': subj['subj_name'], 'level': subj['level']})
        return data
        
    def delete_student(self, record):
        """Deletes a student's subject.
        record = {'student_name': ..., 'subj_name': ..., 'level': ...}
        """
        # check if subject exists and retrieve subject_id
        subj = {}
        subj['subj_name'] = record['subj_name']
        subj['level'] = record['level']
        subj_id_list = self._subj_is_exist((subj,))
        if not subj_id_list:
            return False
        subj_id = subj_id_list[0]

        # retrieve student_id
        student_id = self._retrieve_id('Students', record['student_name'], 'student_name', 'student_id')
        if not student_id:
            return False
        
        # check if student takes that subject
        if not self._is_exists('Students-Subjects', 'student_id', student_id, 'subj_id', subj_id):
            return False
        
        # delete student-subject record
        query = f"""
                DELETE FROM 'Students-Subjects'
                WHERE student_id = ?
                AND subj_id = ?;
                """
        values = (student_id, subj_id)
        self._execute(query, values)
        return
            

class CCAs(Collection):
    """
    CCAs Collection

    Methods:
    --------
    add(record)
    add_student(record)
    get(cca_name)
    get_student(student_name)
    update(cca_name, record)
    update_student(record)
    delete(cca_name)
    delete_student(student_name, cca_name)
    """
    def __init__(self):
        super().__init__("CCAs")

    def add(self, record):
        """Adds a CCA record to the database."""
        # check if CCA exists
        if self._is_exist(self._tblname, "cca_name", record["cca_name"]):
            return False

        # add CCA record
        query = f"""
                INSERT INTO '{self._tblname}' (
                    'cca_name', 'type'
                ) VALUES (:cca_name, :type);
                """
        self._execute(query, record)
        return

    def add_student(self, record):
        """Adds a student to a CCA.
        record = {'student_name': ..., 'cca_name': ..., 'role': ...}
        """
        # check if student/cca exists and retrive ids
        record["student_id"] = self._retrieve_id("Students", record["student_name"], "student_name", "student_id", like=True)
        record["cca_id"] = self._retrieve_id("CCAs", record["cca_name"], "cca_name", "cca_id", like=True)
        
        if record["student_id"] == False or record['cca_id'] == False:
            return False
        
        #check if student is already in that cca
        if self._is_exist('Students-CCAs', 'student_id', record['student_id'], 'cca_id', record['cca_id']):
            return False

        # otherwise add student-cca record
        query = """
                INSERT INTO 'Students-CCAs' (
                    'student_id', 'cca_id', 'role'
                ) VALUES (:student_id, :cca_id, :role);
                """
        self._execute(query, record)
        return
        
    def get(self, cca_name):
            """Returns a CCA's details."""
            # retrieve CCA record
            query = """
                    SELECT *
                    FROM 'CCAs'
                    WHERE cca_name LIKE ?;
                    """
            values = ('%'+cca_name+'%',)
            row = self._return(query, values, multi=False)
            if row is None:
                return False
            
            # convert data to dictionary
            field_names = row.keys()
            data = {}
            for i, elem in enumerate(field_names):
                data[elem] = row[i]
            return data
        
    def get_student(self, student_name, cca_name=None):
        """Returns a list of dict of student's CCAs (if student_cca is None)
        Returns False if student does not have any ccas.
        Returns specific cca for student if student_cca is specified
        """
        data = []

        # retrieve cca_id and role
        if cca_name is not None:
            query = """
                SELECT 
                    'CCAs'.'cca_name' AS 'cca_name',
                    'Students-CCAs'.'role' AS 'role',
                    'Students'.'student_name' AS 'student_name'
                FROM 'Students'
                INNER JOIN 'Students-CCAs'
                ON 'Students'.'student_id' = 'Students-CCAS'.'student_id'
                INNER JOIN CCAs
                ON 'CCAs'.'cca_id' = 'Students-CCAs'.'cca_id'
                WHERE 'Students'.'student_name' LIKE ? AND 'CCAs'.'cca_name' LIKE ?;
                """
            values = ('%'+student_name+'%', '%'+cca_name+'%',)
        else:
            query = """
                    SELECT 
                        'CCAs'.'cca_name' AS 'cca_name',
                        'Students-CCAs'.'role' AS 'role'
                    FROM 'Students'
                    INNER JOIN 'Students-CCAs'
                    ON 'Students'.'student_id' = 'Students-CCAS'.'student_id'
                    INNER JOIN CCAs
                    ON 'CCAs'.'cca_id' = 'Students-CCAs'.'cca_id'
                    WHERE student_name LIKE ?;
                    """

            values = ('%'+student_name+'%',)
        row = self._return(query, values, multi=True)

        #check if student have any ccas at all
        if row == []:
            return False

        for cca in row:
            record = {}
            record['cca_name'] = cca['cca_name']
            record['role'] = cca['role']
            if cca_name is not None:
                record['student_name'] = cca['student_name']
            data.append(record)

        return data

    def update(self, cca_name, record):
        """Updates an acitivty's record."""
        # check if cca exists
        if not self._is_exist(self._tblname, "cca_name", cca_name):
            return False

        # update cca record
        query = f"""
                UPDATE '{self._tblname}' SET
                    'cca_name' = ?,
                    'type' = ?
                WHERE cca_name = ?;
                """
        values = (record["new_cca_name"], record["new_type"], cca_name)
        self._execute(query, values)
        return

    def update_student(self, record):
        """Updates a student's CCA record (update role only).
        record = {'student_name': ..., 'cca_name': ..., 'role': ...}
        """
        # retrieve student_id
        student_id = self._retrieve_id("Students", record["student_name"], "student_name", "student_id", like=True)
        
        # check if student in Students-CCAs
        if not self._is_exist("Students-CCAs", "student_id", student_id):
            return False
            
        # retrieve cca_id
        cca_id = self._retrieve_id("CCAs", record["cca_name"], "cca_name", "cca_id")

        # update student-cca record
        query = """
                UPDATE 'Students-CCAs' SET
                    'role' = ?
                WHERE student_id = ? AND cca_id = ?;
                """
        values = (record["role"], student_id, cca_id)
        self._execute(query, values)
        return

    def delete(self, cca_name):
        """Deletes a CCA record."""
        # check if CCA exists
        if not self._is_exist(self._tblname, "cca_name", cca_name):
            return False

        # retrieve cca_id
        cca_id = self._retrieve_id(self._tblname, cca_name, "cca_name", "cca_id")

        # delete from Students-CCAs and CCAs table
        tblnames = ["Students-CCAs", "CCAs"]
        for tblname in tblnames:
            query = f"""
                    DELETE FROM '{tblname}'
                    WHERE cca_id = ?;
                    """
            values = (cca_id,)
            self._execute(query, values)
        return
        
    def delete_student(self, student_name, cca_name):
        """Deletes a student's CCA record"""
        # retrieve student_id
        student_id = self._retrieve_id("Students", student_name, "student_name", "student_id")
        
        # check if student in Students-CCAs
        if not self._is_exist("Students-CCAs", "student_id", student_id):
            return False
            
        # retrieve cca_id
        cca_id = self._retrieve_id(self._tblname, cca_name, "cca_name", "cca_id")

        # delete student-cca record
        query = """
                DELETE FROM 'Students-CCAs'
                WHERE student_id = ?
                AND cca_id = ?;
                """
        values = (student_id, cca_id)
        self._execute(query, values)
        return

        
class Activities(Collection):
    """
    Activities Collection.

    Methods:
    --------
    add(record)
    add_student(record)
    get(activity_name)
    get_student(student_name)
    update(activity_name, record)
    update_student(record)
    delete(activity_name)
    delete_student(student_name, activity_name)
    """
    def __init__(self):
        super().__init__("Activities")

    def add(self, record):
        """Adds an activity record into the database."""
        # check if activity exists
        if self._is_exist(self._tblname, "activity_name", record["activity_name"]):
            return False

        # add activity record
        query = f"""
                INSERT INTO '{self._tblname}' (
                    'activity_name', 'start_date', 'end_date', 'description'
                ) VALUES (:activity_name, :start_date, :end_date, :description);
                """
        self._execute(query, record)
        return

    def add_student(self, record):
        """Adds a student to an activity.
        record = {'student_name': ..., 'activity_name': ..., 'role': ..., 'award: ...',
        'hours': ...}
        """
        # check if student/activity exists and retrive ids
        record["student_id"] = self._retrieve_id("Students", record["student_name"], "student_name", "student_id", like=True)
        record["activity_id"] = self._retrieve_id("Activities", record["activity_name"], "activity_name", "activity_id", like=True)
        
        if record["student_id"] == False or record['activity_id'] == False:
            return False

        #check if student already linked to activity
        if self._is_exist('Students-Activities', 'student_id', record['student_id'], 'activity_id', record['activity_id']):
            return False

        # add student-activity record
        query = """
                INSERT INTO 'Students-Activities' (
                    'student_id', 'activity_id', 'role', 'award', 'hours'
                ) VALUES (:student_id, :activity_id, :role, :award, :hours);
                """
        self._execute(query, record)
        return

    def get(self, activity_name):
        """Returns an activity's details."""
        # retrieve activity record
        query = f"""
                SELECT *
                FROM '{self._tblname}'
                WHERE activity_name LIKE ?;
                """
        values = ('%'+activity_name+'%',)
        row = self._return(query, values, multi=False)
        if row is None:
            return False

        # convert data into dictionary
        field_names = row.keys()
        data = {}
        for i, elem in enumerate(field_names):
            data[elem] = row[i]
        return data
        
    def get_student(self, student_name, activity_name=None):
        """
        Return a list of student's activity records.
        Return False if no records found
        Return a specific record if activity_name is specified
        """
        data = []
            
        # retrieve activity_id, role, award, hours, activity_name
        if activity_name is not None:
            query = """
                SELECT
                    'Activities'.'activity_name',
                    'Students-Activities'.'role',
                    'Students-Activities'.'award',
                    'Students-Activities'.'hours',
                    'Students'.'student_name'
                FROM 'Students'
                INNER JOIN 'Students-Activities'
                ON 'Students'.'student_id' = 'Students-Activities'.'student_id'
                INNER JOIN 'Activities'
                ON 'Activities'.'activity_id' = 'Students-Activities'.'activity_id'
                WHERE 'Students'.'student_name' LIKE ? AND 'Activities'.'activity_name' LIKE ?;
                """
            values = ('%'+student_name+'%', '%'+activity_name+'%',)
        else:
            query = """
                    SELECT
                        'Activities'.'activity_name',
                        'Students-Activities'.'role',
                        'Students-Activities'.'award',
                        'Students-Activities'.'hours'
                    FROM 'Students'
                    INNER JOIN 'Students-Activities'
                    ON 'Students'.'student_id' = 'Students-Activities'.'student_id'
                    INNER JOIN 'Activities'
                    ON 'Activities'.'activity_id' = 'Students-Activities'.'activity_id'
                    WHERE student_name LIKE ?;
                    """
            values = ('%'+student_name+'%',)
        row = self._return(query, values, multi=True)

        # check if student has an activity
        if row == []:
            return False

        for activity in row:
            record = {}
            if activity_name is not None:
                record["student_name"] = activity['student_name']
            record["role"] = activity["role"]
            record["award"] = activity["award"]
            record["hours"] = activity["hours"]
            record["activity_name"] = activity["activity_name"]
            data.append(record)
            
        return data

    def update(self, activity_name, record):
        """Updates an acitivty's record."""
        # check if activity exists
        if not self._is_exist(self._tblname, "activity_name", activity_name):
            return False

        # update activity record
        query = f"""
                UPDATE '{self._tblname}' SET
                    'activity_name' = ?,
                    'start_date' = ?,
                    'end_date' = ?,
                    'description' = ?
                WHERE activity_name = ?;
                """
        values = (record["new_activity_name"], record["new_start_date"], record["new_end_date"], record["new_description"], activity_name)
        self._execute(query, values)
        return

    def update_student(self, record):
        """Updates a student's activity record (updates role, award, hours).
        record = {'student_name': ..., 'activity_name', 'award': ..., 'role': ..., 
        'hours': ...}
        """
        # retrieve student_id
        student_id = self._retrieve_id("Students", record["student_name"], "student_name", "student_id")
        
        # check if student in Students-Activities
        if not self._is_exist("Students-Activities", "student_id", student_id):
            return False
            
        # retrieve activity_id
        activity_id = self._retrieve_id(self._tblname, record["activity_name"], "activity_name", "activity_id")

        # update student-activity record
        query = """
                UPDATE 'Students-Activities' SET
                    'role' = ?,
                    'award' = ?,
                    'hours' = ?
                WHERE student_id = ?
                AND activity_id = ?;
                """
        values = (record["role"], record["award"], record["hours"], student_id, activity_id)
        self._execute(query, values)
        return

    def delete(self, activity_name):
        """Deletes an activity record."""
        # check if activity exists
        if not self._is_exist(self._tblname, "activity_name", activity_name):
            return False

        # retrieve activity_id
        activity_id = self._retrieve_id(self._tblname, activity_name, "activity_name", "activity_id")

        # delete from Students-Activities and Activities table
        tblnames = ["Students-Activities", "Activities"]
        for tblname in tblnames:
            query = f"""
                    DELETE FROM '{tblname}'
                    WHERE activity_id = ?;
                    """
            values = (activity_id,)
            self._execute(query, values)
        return
        
    def delete_student(self, student_name, activity_name):
        """Deletes a student's activity record"""
        # retrieve student_id
        student_id = self._retrieve_id("Students", student_name, "student_name", "student_id")
        
        # check if student in Students-Activities
        if not self._is_exist("Students-Activities", "student_id", student_id):
            return False
            
        # retrieve activity_id
        activity_id = self._retrieve_id(self._tblname, activity_name, "activity_name", "activity_id")

        # delete student-activity record
        query = """
                DELETE FROM 'Students-Activities'
                WHERE student_id = ?
                AND activity_id = ?;
                """
        values = (student_id, activity_id)
        self._execute(query, values)
        return