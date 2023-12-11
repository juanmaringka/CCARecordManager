from flask import Flask, render_template, request
from datetime import datetime
from storage import Students, Classes, Subjects, CCAs, Activities

classes = Classes()
subjects = Subjects()
ccas = CCAs()
activities = Activities()
students = Students()

app = Flask(__name__)


def validate_date(start_date: str, end_date=''):
    """
    Validate a given dates based on ISO 8601 YYYY-MM-DD format
    Start date must be before end_date
    """
    #strip the dates
    start_date = start_date.strip()
    end_date = end_date.strip()
    
    #check for start date
    format = "%Y-%m-%d"
    try:
        res1 = datetime.strptime(start_date, format)
    except ValueError:
        res1 = False
    
    #check for end date if it is not empty
    if end_date != '':
        try:
            res2 = datetime.strptime(end_date, format)
        except ValueError:
            res2 = False
    else:
        res2 = True

    if res1 and res2:
        #check if start_date is later than end_date
        if end_date != '' and (res1 > res2):
            return False
        
        #check for end date if it is not empty
        if end_date != '':
            year, month, day = end_date.split('-')
            if len(year) != 4 or len(month) != 2 or len(day) != 2:
                return False
        
        #check length for start date
        year, month, day = start_date.split('-')
        if len(year) == 4 and len(month) == 2 and len(day) == 2:
            return True
        
    return False


def has_error(data: dict):
    '''
    Returns an error message for the last value that is empty, otherwise returns an empty string
    Exception for end date, award and hours which are optional
    '''
    for key, value in data.items():
        #end date, award and hours can be empty
        if value == '' and key not in ['End Date', 'Award', 'Hours']:
            return f'Please do not leave the {key} empty.'
    return ''


def strip(data: dict):
    """Strips all the values in a dict"""
    for key, value in data.items():
        data[key] = value.strip()
    return data

@app.route('/')
def index():
    '''
    displays the index page at /
    '''
    return render_template('index.html')


@app.route('/add', methods=['GET', 'POST'])
def add():
    page_type = 'new'
    title = 'What would you like to add?'
    form_meta = {'action': '/add?add', 'method': 'get'}
    form_data = {'choice': ''}
    choices = ['CCA', 'Activity']
    button = ''
    tdtype = ''
    error = ''

    if request.args.get('choice') in choices:
        choice = request.args.get('choice')
        tdtype = 'text'
        button = 'Submit'
        if choice == 'CCA':
            form_data = {'Name': '', 'CCA Type': ''}
            title = 'Add CCA:'
            page_type = 'form'
            form_meta = {'action': '/add?confirm', 'method': 'post'}
        else:
            form_data = {
                'Name': '',
                'Start Date': '',
                'Description': '',
                'End Date': ''
            }
            title = 'Add Activity:'
            page_type = 'form'
            form_meta = {'action': '/add?confirm', 'method': 'post'}

    if 'confirm' in request.args:
        page_type = 'confirm'
        title = 'Are the following details correct?'
        tdtype = 'text'
        button = 'Submit'
        form_data = strip(dict(request.form))
        error = has_error(form_data) 
        if 'Description' in form_data.keys():  # validate date if activity
            start_date = form_data['Start Date']
            end_date = form_data['End Date']
            if not validate_date(start_date, end_date):
                error = 'Please ensure the date is in the correct format (YYYY-MM-DD).'
                if end_date != '':
                    error += ' Start Date should also be before End Date.'

        if error:  # if there is an error, return to new form page
            form_meta = {'action': '/add?confirm', 'method': 'post'}
            tdtype = 'text'
            page_type = 'form'
        else:  # otherwise, move on
            form_meta = {'action': '/add?result', 'method': 'post'}
            tdtype = 'hidden'
            button = 'Yes'

    if 'result' in request.args:
        ## check if record is present
        form_data = strip(dict(request.form))
        choice = 'CCA' if 'CCA Type' in form_data.keys() else 'Activity'
        if choice == 'CCA':
            res = ccas.add({'cca_name': form_data['Name'],
                            'type': form_data['CCA Type']})
        else:
            res = activities.add({'activity_name': form_data['Name'],
                           'start_date': form_data['Start Date'],
                           'description': form_data['Description'],
                           'end_date': form_data['End Date']})
                            
        if res != False:
            page_type = 'success'
            title = 'You have successfully added the following record!'
        else:
            error = f'The {choice} {form_data["Name"]} already exists'
            form_meta = {'action': '/add?confirm', 'method': 'post'}
            tdtype = 'text'
            page_type = 'form'
            button = 'Submit'

    return render_template('add.html',
                           page_type=page_type,
                           title=title,
                           form_meta=form_meta,
                           form_data=form_data,
                           choices=choices,
                           button=button,
                           tdtype=tdtype,
                           error=error)


@app.route('/view', methods=['GET', 'POST'])
def view():
    page_type = 'new'
    title = 'What would you like to view?'
    choices = ['Student', 'Class', 'CCA', 'Activity']
    form_meta = {'action': '/view?view', 'method': 'get'}
    form_data = {'choice': ''}
    table_header = {}
    list_header = ()
    data = {}
    choice = ''
    key = ''
    file = 'view.html'
    error = ''
    list_of_dicts = [] # contain the additional tables 
                       #list of lists; one element inside is [header, data:dict]

    if request.args.get('choice') in choices:
        choice = request.args.get('choice')
        page_type = 'search'
        title = f'Which {choice} you would like to search for?'
        ## .get the appropriate data from idk where juan pls help
        form_meta = {'action': '/view?searched', 'method': 'post'}

    if 'searched' in request.args:
        # get data from databases, data u get will be a dictionary, use the search method
        key = list(request.form.keys())[0]
        form_data = dict(request.form)
        # key is Student Class CCA or Activity
        if key == 'Student':
            table_header = {'student_name': 'Student Name',
                            'age': 'Age',
                            'year_enrolled': 'Year Enrolled',
                           'grad_year': 'Graduation Year',
                           'class_name': 'Class',
                           'student_id': 'Student ID'}
            data = students.get(form_data[key])
            name = form_data['Student'].strip()

            #check if student has any ccas or activities at all
            #then on webpage print 'There are no CCAs/Activities linked to this student'
            list_of_dicts.append(['Subjects', 
                                  subjects.get_student(name), 
                                 ('Subject', 'Level')])
            list_of_dicts.append(['CCAs', 
                                  ccas.get_student(name),
                                 ('CCA', 'Role')])
            list_of_dicts.append(['Activities', 
                                  activities.get_student(name),
                                  ('Activity', 'Role', 'Award', 'Hours')])

        # info = [{'subj_name':'gp', 'subj_lvl': 'h1'}, {}]
            
        elif key == 'Class':
            name = form_data['Class'].strip()
            table_header = {'class_name': 'Class',
                            'level': 'Level',
                           'class_id': 'Class ID'}
            list_header = ('Student ID', 'Student Name')
            data = classes.get_info(form_data[key])
            list_of_dicts.append(['Class List', classes.get(name), list_header])
            
        elif key == 'CCA':
            name = form_data[key].strip()
            table_header = {'cca_name': 'CCA Name',
                            'type': 'Type',
                           'cca_id': 'CCA ID'}
            data = ccas.get(name)
            
        else:
            name = form_data[key].strip()
            table_header = {'activity_name': 'Activity Name',
                            'start_date': 'Start Date',
                           'end_date': 'End Date',
                           'description': 'Description',
                           'activity_id': 'Activity ID'}
            data = activities.get(name)

        if data and name != '': # if in database
            title = f'{key}: {form_data[key]}'
            page_type = 'result'
            # get from database
        else:  # if not in database, user will re-enter the form
            page_type = 'search'
            error = f'{key} does not exist'
            choice = key
            title = f'Which {key} you would like to search for?'
            form_meta = {'action': '/view?searched', 'method': 'post'}

    return render_template(file,
                           choices=choices,
                           page_type=page_type,
                           form_meta=form_meta,
                           form_data=form_data,
                           data=data,
                           title=title,
                           choice=choice,
                           key=key,
                           error=error,
                           table_header=table_header,
                           list_of_dicts=list_of_dicts,
                           list_header=list_header)


@app.route('/edit', methods=['GET', 'POST'])
def edit():
    page_type = 'new'
    title = 'What would you like to edit?'
    choices = [
        'Add CCA Member', 'Add Activity Participant', 'Edit CCA Member',
        'Edit Activity Participant', 'Remove CCA Member',
        'Remove Activity Participant'
    ]
    form_meta = {'action': '/edit?edit', 'method': 'get'}
    form_data = {'Student Name': ''}
    choice = ''
    key = ''
    error = ''
    type = ''
    action = 'remove'
    tdtype = 'text'

    if request.args.get('choice') in choices:
        choice = request.args.get('choice')
        page_type = 'search'
        type = 'CCA' if choice in [
            'Add CCA Member', 'Edit CCA Member', 'Remove CCA Member'
        ] else 'Activity'
        if choice in ['Add CCA Member', 'Add Activity Participant']:
            action = 'add'
            #default values
            form_data['Role'] = 'Member' if type == 'CCA' else 'Participant'
            if type == 'Activity':
                form_data['Award'] = ''
                form_data['Hours'] = ''
        elif choice in ['Edit CCA Member', 'Edit Activity Participant']:
            action = 'edit'
        # action will remain as removed if its remove cca member/remove activity participant
        form_data[type] = ''
        title = f'Which student do you want to {action} from the {type}?' if action != 'add' else f'Which student do you want to {action} to the {type}?'
        form_meta = {'action': '/edit?searched', 'method': 'post'}

    if 'searched' in request.args:
        action = request.form['action']
        page_type = 'verify'
        form_data = dict(request.form)
        form_data.pop('action')
        error = has_error(form_data)
        type = 'Activity' if 'Activity' in form_data.keys() else 'CCA'

        if error == '':
            if type == 'Activity' and action == 'add':
                # there is no student in specified activity
                if activities.get_student(form_data['Student Name'], form_data['Activity']): 
                    error = 'Student already exists'
                elif not activities.get(form_data['Activity']):
                    error = 'Activity does not exist'
                elif not students.get(form_data['Student Name']):
                    error = 'Student does not exist'
            elif type == 'Activity' and action != 'add':
                if not activities.get_student(form_data['Student Name'], form_data['Activity']):
                    error = 'Student does not exist'
            elif type == 'CCA' and action == 'add':
                # there is no student in specified activity
                if ccas.get_student(form_data['Student Name'], form_data['CCA']): 
                    error = 'Student already exists'
                elif not ccas.get(form_data['CCA']):
                    error = 'CCA does not exist'
                elif not students.get(form_data['Student Name']):
                    error = 'Student does not exist'
            elif type == 'CCA' and action != 'add':
                if not ccas.get_student(form_data['Student Name'], form_data['CCA']):
                    error = 'Student does not exist'
                
        if error:
            form_meta = {'action': '/edit?searched', 'method': 'post'}
            tdtype = 'text'
            page_type = 'search'
            title = f'Which student do you want to {action} from the {type}?' if action != 'add' else f'Which student do you want to {action} to the {type}?'
        else:
            if action != 'add':
                name = request.form['Student Name']
                
                if type == 'Activity':
                    record = activities.get_student(name, request.form[type])[0]
                    form_data['Award'] = record['award']
                    form_data['Hours'] = record['hours']  
                else:
                    record = ccas.get_student(name, request.form[type])[0]
                    form_data['CCA'] = record['cca_name']
                form_data['Student Name'] = record['student_name']
                form_data['Role'] = record['role']
                    
            form_meta = {'action': '/edit?success', 'method': 'post'}

            if action == 'add':
                title = 'Are you sure you want to add the following record?'
                tdtype = 'hidden'
                #get the correct values for the confirm page
                if type == 'Activity':
                    form_data['Activity'] = activities.get(form_data['Activity'])['activity_name']
                else:
                    form_data['CCA'] = ccas.get(form_data['CCA'])['cca_name']
                form_data['Student Name'] = students.get(form_data['Student Name'])['student_name']
            elif action == 'edit':
                title = 'Please edit the following details'
            else:
                title = 'Are you sure you want to delete the this record?'
                tdtype = 'hidden'

    if 'success' in request.args:
        action = request.form['action']
        form_data = dict(request.form)
        form_data.pop('action')
        type = 'CCA' if 'CCA' in form_data.keys() else 'Activity'

        if type == 'Activity':
            record = {'activity_name': form_data['Activity'],
                     'student_name': form_data['Student Name'],
                     'role': form_data['Role'],
                     'award': form_data['Award'],
                     'hours': form_data['Hours']}
        else:
            record = {'cca_name': form_data['CCA'],
                     'student_name': form_data['Student Name'],
                     'role': form_data['Role']}
        
        if action == 'add': # add form_data into database
            word = 'added'
            if type == 'Activity':
                activities.add_student(record) 
            else:
                ccas.add_student(record) 
            
        elif action == 'edit': # edit new data
            word = 'edited'
            if type == 'Activity':
                activities.update_student(record)
            else:
                ccas.update_student(record)
        
        elif action == 'remove': # remove from database
            word = 'removed'
            if type == 'Activity':
                activities.delete_student(form_data['Student Name'], 
                                          form_data['Activity'])
            else:
                ccas.delete_student(form_data['Student Name'],
                                    form_data['CCA'])
            
        page_type = 'success'
        title = f'The following record has been {word}!'

    return render_template('edit.html',
                           page_type=page_type,
                           title=title,
                           choice=choice,
                           form_meta=form_meta,
                           choices=choices,
                           key=key,
                           error=error,
                           form_data=form_data,
                           action=action,
                           tdtype=tdtype)

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(error):
    return render_template('500.html'), 500

@app.route('/help', methods=['GET'])
def help():
    faq = {
        'How do I use this website?':
        """The Student CCA Portal allows you to add a CCA/Activity, view Student/Class/CCA/Activity and edit a CCA Member/Activity Participant
        Viewing a Student would give you not only the student particulars, but also the Subjects they take and the CCAs and Activities they are in! 
        Viewing a Class would give you the details of the Class, and also the students in the Class.""",
        'Do I need to fill in the ENTIRE NAME when I want to search/edit a record?':
        """
        Nope, you don't have to do that at all. You only have to enter part of the name and the record would be shown! (saves your time and your brain capacity right 😎). Make sure not to name your records similarly to existing ones in the database! (otherwise it'll be lost in the database)
        """
    }
    return render_template('help.html',
                           title='Help Section',
                          faq=faq,
                          length=len(faq.items()))