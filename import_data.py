import csv
from storage import Students, Classes, CCAs

classes = Classes()
students = Students()

with open("student.csv", 'r') as f:
    students_list = csv.DictReader(f)
    for student in students_list:
        record = {}
        record['student_name'] = student['student_name']
        record['class_name'] = student['class_id']
        record['age'] = 18
        record['year_enrolled'] = student['year_enrolled']
        record['grad_year'] = 2023

        if classes.get(record['class_name']) == False:
            classes.add({'class_name': record['class_name'], 'level': 'J2'})
        students.add(record)
students.display_all()        

ccas = CCAs()
with open('cca.csv') as f:
    cca_list = csv.DictReader(f)
    for cca in cca_list:
        record = {}
        record['cca_name'] = cca['name']
        record['type'] = cca['type']
        ccas.add(record)
ccas.display_all()
            
        
        
    