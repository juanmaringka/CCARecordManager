from storage import Students, Classes, Subjects, CCAs, Activities

from storage import Students, Classes, Subjects, CCAs, Activities

students = Students()
activities = Activities()
subjects = Subjects()
ccas = CCAs()

subj_list = [{'subj_name': 'GP', 'level': 'H1'},
            {'subj_name': 'PHY', 'level': 'H3'}]

record = {'student_name': 'mOSES', 'subj_list':subj_list}
#print(subjects.add_student(record))
#print(subjects.add_student(record))
ccas.delete('playstation')
print(ccas.get('chinese orchestra'))
activities.display_all()
ccas.display_all()
