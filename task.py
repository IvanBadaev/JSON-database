import json
import io

class JSONDatabase:
    def __init__(self, filename):
        self.filename : str = filename

    def connect(self):
        return DBSession(self.filename)

class DBSession:

    def __init__(self, filename):

        self.filename : str = filename

        JSONfile = io.open(f'src/{self.filename}.json', mode='r', encoding='utf-8')
        self.content : list = json.loads(JSONfile.read())
        JSONfile.close()
        
        self.console : DBConsoleInterface = DBConsoleInterface()

        self.attributeInput = InputValidator('Type the parameter by which you want to find the book. \n', self.validateAttribute)
        self.attributeUpdateInput = InputValidator('Type the attribute of the book you wish to update. \n', self.validateAttribute)
        self.queryIdInput = InputValidator('Choose the book you would like to update by id.\n', self.validateQueryID)
        self.yearInput = InputValidator('Enter book release year.\n', self.validateYear)
        self.borrowersInput = InputValidator('Enter names of borrowers in format "Ivan, Oleg, Dmitriy"...\n', self.validateBorrowedNames)

        
        self.menu()
        
    def menu(self):
        
        possible_actions = ['create', 'show_all', 'search', 'update', 'delete', 'quit']

        print(f'\nJSON DB session started. All changes will be saved to JSON after "quit" command.\nFollowing commands are available: {', '.join(possible_actions)}. \n')
        self.console.printLine()

        while True:
            user_action = input('\nEnter a DB action\n\n')
            if (user_action not in possible_actions):
                print(f'ValueError: command does not exist. Possible commands: {', '.join(possible_actions)}\n')
            elif (user_action == 'create'):
                self.create()
            elif (user_action == 'show_all'):
                self.showAll()
            elif (user_action == 'search'):
                self.filter()
            elif (user_action == 'update'):
                self.update()
            elif (user_action == 'delete'):
                self.delete()
            elif (user_action == 'quit'):
                self.quit()
                break
            else:
                print('Internal Error: command exists, but is not implemented.')

    # -- CRUD in menu --
        
    def create(self):

        author = input('Enter book author.\n')
        title = input('Enter book title.\n')
        genre = input('Enter book genre.\n')
        year = self.yearInput.modal()
        borrowed_by = self.borrowersInput.modal()

        new_book = Book(self, title, author, genre, year, borrowed_by)
        self.content.append(vars(new_book))

        print('Successfully created entry:')
        self.console.printTable(vars(new_book))

    def showAll(self):
        self.console.printTable(self.content)
    
    def filter(self):
        self.search(leave_one = False)
    
    def update(self):
        updateQuery = self.search()
        id = updateQuery.get('id')
        updated_entry = updateQuery.get('selectedEntry')
        key = self.attributeUpdateInput.modal(True)
        if key == 'Year':
            new_value = self.yearInput.modal()
        elif key == "BorrowedBy":
            new_value = self.borrowersInput.modal()
        else:
            new_value = input('Type the value you would like to insert')
        updated_entry.update({key : new_value})
        self.content = list(map(lambda book_item : updated_entry if book_item["BookID"] == id else book_item, self.content))
        print('Successfully updated entry:')
        self.console.printTable(updated_entry)

    def delete(self):
        deleteQuery = self.search()
        confirm = input('Do you wish to proceed with deleting an entry? To abort, type "back".')
        if confirm == 'back':
            return
        id = deleteQuery.get('id')
        self.content = list(filter(lambda entry : entry["BookID"] == id, self.content))
        print(f'Deleted entry:')
        self.console.printTable(deleteQuery.get('selectedEntry'))

    def quit(self):
        jsonContent = json.dumps(self.content)
        JSONfile = io.open(f'src/{self.filename}.json', mode='w', encoding='utf-8')
        JSONfile.write(jsonContent)
        JSONfile.close()
        print('\nJSON DB session ended. Changes saved.\n')
        self.console.printLine()
    
    # -- Input validation logic --

    def validateBorrowedNames(self, names : str):
        namesList = names.split(', ')
        namesList = list(map(lambda name : name.strip().capitalize(), namesList))
        return namesList

    def validateAttribute(self, input_attribute : str, disallow_id : tuple | bool = False):
        input_attribute_lowercase = input_attribute.lower().strip()
        if disallow_id:
            disallow_id = disallow_id[0]
            searchable_attributes = ['title', 'author', 'genre', 'year', 'borrowedby']
        else:
            searchable_attributes = ['bookid', 'title', 'author', 'genre', 'year', 'borrowedby']
        if input_attribute not in searchable_attributes:
            print(f'\nError: specified attribute does not exist or is not acceptable.\nAccepted attributes: {searchable_attributes}')
            self.console.printLine()
            return None
        else:
            search_sanitize_dictionary = {
                'bookid' : 'BookID',
                'title' : 'Title',
                'author' : 'Author',
                'genre' : 'Genre',
                'year' : 'Year',
                'borrowedby' : 'BorrowedBy',
            }
            return search_sanitize_dictionary[input_attribute_lowercase]

    def validateQueryID(self, input_id, found_entries):
        try:
            int(input_id)
        except ValueError:
            print('\nValueError: Please, provide an integer value for a book ID.')
        selected_entry = filter(lambda entry : entry["BookID"] == id, found_entries).pop()
        if (selected_entry):
            return input_id, selected_entry
        else:
            print('\nValueError: an entry with the specified ID does not exist in a query. Please, enter an existing ID\n')
            print(f'Existing entries filtered by query: {found_entries}')
            self.console.printLine()
            return None

    def validateYear(self, user_year):
        try:
            int(user_year)
            return user_year
        except ValueError:
            print('\nValueError: a book year must be an integer. Please, provide an integer value.\n')
            self.console.printLine()
            return None
        

    # -- Query logic --
        
    def getLastID(self):
        if not len(self.content):
            return 0
        self.content.sort(key=lambda item : item["BookID"])
        lastID = self.content[-1]["BookID"]
        return lastID
    
    def search(self, leave_one : bool = True):
        sanitized_attribute = self.attributeInput.modal()
        if not len(self.content):
            print('Unfortunately, there are no entries in the DB at the moment.')
            return
        value = input('Type the search value\n')
        found_entries, exact_matches = self.query(sanitized_attribute, value)
        if not len(found_entries):
            print(f'Unfortunately, no books were found with parameters {sanitized_attribute} = {value}')
        else:
            if (exact_matches):
                print(f'Query {sanitized_attribute} = {value}; Found the following books:')
            else:
                print(f'Unfortunately, no direct matches were found. Query: {sanitized_attribute} = {value}. Similar results:')
            self.console.printTable(found_entries)
            if len(found_entries) > 1 and leave_one:
                id, selected_entry = self.queryIdInput.modal(found_entries)
                return {"entryId" : id, "selectedEntry" : selected_entry}
            elif leave_one:
                selected_entry = found_entries.pop()
                id = selected_entry["BookID"]
                return {"entryId" : id, "selectedEntry" : selected_entry}
            else:
                return found_entries
    
    def query(self, sanitized_attribute : str, user_value : str):
        
        user_value_lowercase = user_value.lower().strip()
        result = []
        result_similars = []
        for book_entry in self.content:
            loop_value = book_entry.get(sanitized_attribute)
            if type(loop_value) != list:
                loop_value = str(book_entry.get(sanitized_attribute)).lower().strip()
                if loop_value == user_value_lowercase:
                    result.append(book_entry)
                elif user_value_lowercase in loop_value or loop_value in user_value_lowercase:
                    result_similars.append(book_entry)
            else:
                for name in loop_value:
                    if user_value_lowercase == name.strip().lower():
                        result.append(book_entry)
        
        if len(result):
            return result, True
        else:
            return result_similars, False

class Book:
    def __init__(self, DBSession : DBSession, Title : str, Author : str, Genre : str, Year : int, BorrowedBy : list):

        self.BookID = DBSession.getLastID() + 1
        self.Title = Title
        self.Author = Author
        self.Genre = Genre
        self.Year = Year
        self.BorrowedBy = BorrowedBy

class InputValidator:
    def __init__(self, inputMessage : str, validateFunc):
        self.validateFunc = validateFunc
        self.inputMessage = inputMessage
    
    def modal(self, *args):
        while True:
            userValue = input(self.inputMessage)
            if (args):
                sanitizedValue = self.validateFunc(userValue, args)
            else:
                sanitizedValue = self.validateFunc(userValue)
            if (sanitizedValue):
                break
        return sanitizedValue


# Beautiful output module
    
class DBConsoleInterface:

    def __init__(self):
        self.tableCellsLengthMap = {
            "BookID" : 8,
            "Title" : 24,
            "Author" : 24,
            "Genre" : 16,
            "Year" : 5,
            "BorrowedBy" : 20
        }
        self.firstEntry = {
            "BookID" : 'Book ID',
            "Title" :  'Title',
            "Author" : 'Author',
            "Genre" : 'Genre',
            "Year" : 'Year',
            "BorrowedBy" : ["Borrowed by"]
        }
        self.length = len(self.tableRow(self.firstEntry))

    def tableCell(self, string : str, cell_length : int):
        whitespace_length = cell_length - len(string)
        if (whitespace_length < 0):
            string = string[0 : cell_length - 2] + '..'
        cellStr = '| ' + string + ' ' * whitespace_length
        return cellStr

    def tableRow(self, entry : dict):

        table_row = ''
        
        for item in entry.items():
            key = str(item[0])
            value = item[1]
            if key == 'BorrowedBy':
                value = ', '.join(value)
            else:
                value = str(item[1])
            table_row += self.tableCell(value, self.tableCellsLengthMap[key])

        table_row += '|'

        return table_row
    
    def printLine(self, length : int = 0):
        if not length:
            length = self.length
        print('-' * length)

    def printPlusLine(self):
        line = '+'
        for cellLength in self.tableCellsLengthMap.values():
            line = line + '-' * (cellLength + 1) + '+'
        print(line)

    def printTableRow(self, table_row, last : bool = False):
        print(table_row)
        if not last:
            print(self.printLine())

    def printTable(self, entries):

        self.printPlusLine()
        print(self.tableRow(self.firstEntry))
        self.printPlusLine()

        if type(entries) == dict:
            print(self.tableRow(entries))
            self.printPlusLine()

        elif type(entries) == list:
            for entry in entries:
                print(self.tableRow(entry))
                self.printPlusLine()


db = JSONDatabase('library')
db.connect()
