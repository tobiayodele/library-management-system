import bcrypt
import tkinter as tk
from tkinter import messagebox
import sqlite3
import re
from datetime import datetime, timedelta

def validate_login():
    #take username and password entry
    entry_username =entered_username.get()
    entry_password=entered_password.get()
    # create object of the member manager class and connect to the members table
    member_manager = MemberManager("members2.db")  
    get_member = member_manager.get_member_by_username(entry_username) 

    if get_member != None:
    #hashes the user entered password using the salt from the hashed password
        if bcrypt.checkpw(entry_password.encode('utf-8'), get_member.hashed_password) == True:
            messagebox.showinfo("Successful Login", "{} has logged into the system, Role is {}.".format(get_member.username,get_member.role.capitalize()))
            root.destroy()  
            
            #open library app window and pass in the user's role
            open_library_app(get_member.role)
        else: 
            messagebox.showerror("Login Failed", "You have entered an incorrect username or password")
    else:    
         messagebox.showerror("Login Failed", "You have entered an incorrect username or password")

class Member:
    def __init__(self, username, email, hashed_password, role="member"):
        self.username = username
        self.email = email
        self.hashed_password = hashed_password
        self.role = role  # 'member' or 'librarian'

#defines book class with public attributes for title, author, genre and ISBN value (all entered as parameters)
class Book:
    def __init__(self, title, author, genre, isbn):
        self.title = title
        self.author = author
        self.genre = genre
        self.isbn = isbn  

class DatabaseManager:
    def __init__(self, db_name):
        #connects to database which is passed in a parameter
        self.conn = sqlite3.connect(db_name)
        self.create_tables()
    def create_tables(self):
       pass
    #closes connection with database
    def close(self):
        self.conn.close()

class MemberManager(DatabaseManager):
    #create the library member table if needed, particularly when run for the first time, prevents error when modifying a database which does not exist.
    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS members
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT UNIQUE NOT NULL,
                      email TEXT UNIQUE NOT NULL,
                      password TEXT NOT NULL,
                      role TEXT NOT NULL)''')  
        self.conn.commit()

    #function to search the database for a certain user and create a member object with their information
    def get_member_by_username(self, username):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT * FROM members WHERE username = ?''', (username,))
        #creates a list of the user information
        row = cursor.fetchone() 
        if row != None:  # if the user is found create a member object with their infomation
            return Member(row[1], row[2], row[3], row[4])
        return None  # if no user 
    
    def get_member_by_id(self, member_id):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT * FROM members WHERE id = ?''', (member_id,))
        #creates a list of the user information
        row = cursor.fetchone() 
        if row != None:  # if the user is found create a member object with their infomation
            return Member(row[1], row[2], row[3], row[4])
        return None  # if no user 
    
    def add_member(self, member):
        #connects to database wtih cursor c
        cursor = self.conn.cursor()
        try:
            # add new user into the members database, using hashed password
            cursor.execute('''INSERT INTO members (username, email, password, role) VALUES (?, ?, ?, ?)''', 
                (member.username, member.email, member.hashed_password, member.role))
            self.conn.commit()
            #grabs the primary key from the last row, i.e. the row that was just added.
            user_id = cursor.lastrowid
            return "The member {} has been added to the system. Its Member ID is {}".format(member.username,user_id)
        except sqlite3.IntegrityError: return "The email address or username you have entered is not unique"
        
   
    
    def delete_member(self, member_id): #delete member from database
        cursor = self.conn.cursor()
        cursor.execute('''DELETE FROM members WHERE id = ?''', (member_id,))
        #if no rows containing the member was found, the user does not exist in the database
        if cursor.rowcount == 0:
            return "You have entered an incorrect Member ID."
        else:
            self.conn.commit()
            return "User {} has been deleted".format(member_id)
        


        
class BookManager(DatabaseManager):
    #create the library books  tables if needed, particularly when run for the first time, prevents error when modifying a database which does not exist.
    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS books
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     title TEXT,
                     author TEXT,
                     genre TEXT,
                     isbn TEXT UNIQUE,
                     checked_in INTEGER DEFAULT 1)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS loans
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     book_id INTEGER,
                     member_id INTEGER,
                     loan_date TEXT,
                     due_date TEXT,
                     returned INTEGER DEFAULT 0,
                     FOREIGN KEY(book_id) REFERENCES books(id),
                     FOREIGN KEY(member_id) REFERENCES members(id))''')
        self.conn.commit()

    def add_book(self, newbook): #add book to database
           
        cursor = self.conn.cursor()
        #attempt to add the book to the books table error from sqlite3 integrity error as the ISBN (the book) is already in the database
        try:
            cursor.execute('''INSERT INTO books (title, author, genre, isbn) VALUES (?, ?, ?, ?)''', 
                (newbook.title, newbook.author, newbook.genre, newbook.isbn))
            self.conn.commit()
            book_id = cursor.lastrowid
            return "The book {} has been added to the system. Its Book ID is {}".format(newbook.title ,book_id)
        except sqlite3.IntegrityError:#ISBN must be unique
            return "You have entered an ISBN which is already in the database."

    def delete_book(self, delete_book_id): #delete book from database using a search of the book id
        cursor = self.conn.cursor()
        cursor.execute('''DELETE FROM books WHERE id = ?''', (delete_book_id,))
        #if no rows containing the book ID was found, the book does not exist in the database
        if cursor.rowcount == 0: 
            return "A book with this Book ID does not exist."
        else:
            self.conn.commit()
            return "The book with ID {} has been deleted".format(delete_book_id)
    
    def search_book_by_title(self, title):# search for books according to the title
        cursor = self.conn.cursor()
        #LIKE so doesnt have to be a direct match (allows for wildcards)
        cursor.execute('''SELECT * FROM books WHERE title LIKE ?''', ('%' + title + '%',)) 
        filteredbooks = cursor.fetchall()
        return filteredbooks
    
    def fetch_all_books(self):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT * FROM books''')# return everything (*) from the books database
        rows = cursor.fetchall()
        #initialises empty list of books and then appends new book objects to the end of that list
        all_books=[]
        for i in range(len(rows)):
            all_books.append(Book(rows[i][1], rows[i][2], rows[i][3], rows[i][4]))
        
        return all_books
    
    def quick_sort(self, books, low, high):           
        if (low < high):
            #like a pre order traversal
            pivot=self.partition(books,low, high) # get the index of the pivot
            self.quick_sort(books,low, pivot-1) # sort the left subset
            self.quick_sort(books, pivot+1, high)# sort the right subset
        return books

    def partition(self,books,low, high):
        pivot=books[low] #first book is the pivot
        leftwall=low#boundary between elements smaller and greater than the pivot
        for i in range(low+1,high+1):
            if books[i].isbn < pivot.isbn:# if curent element is less than the pivot move it to the left of the leftwall
                leftwall +=1
                #swap the current element and the element at indext leftwall
                temp=books[i]
                books[i]=books[leftwall]
                books[leftwall]=temp
        #swap the pivot element with the element at the elft wall
        temp=books[low]
        books[low] = books[leftwall]
        books[leftwall]=temp
        #return indext of the pivot
        return leftwall
        
    def binary_search(self, isbn):
        allbooks = self.fetch_all_books()  # grabs all books, making sure they're all objects
        low=0
        high = len(allbooks) - 1
        allbooks = self.quick_sort(allbooks,low,high)  # sorts all the books for isbn (binary search must be in order) 
        while low <= high:
            mid = (low + high) // 2
            if allbooks[mid].isbn == isbn: #if the mid index isbn = target, it is found
                return allbooks[mid]
            elif allbooks[mid].isbn < isbn:#cut off lower half of the array
                low = mid + 1
            else:
                high = mid - 1 #cut of larger half of the array
        return None
    
    def sort_books_by_genre(self, genre):
        books= self.fetch_all_books()#grabs all the books
        sortedbooks=[]
        for i in range (len(books)):#linear search, if the book's genre matches the target genre add it to the sortedbooks list
            if books[i].genre == genre:
                sortedbooks.append(books[i])
        return sortedbooks


    def merge(self,sortedbooks, low, mid, high):
        left = sortedbooks[low:mid + 1] #create temporary list for left half
        right=sortedbooks[mid+1:high+1] #create temporary list for right half
        loc1 = 0 #pointer for left array
        loc2 = 0 # pointer for right array
        locM = low # pointer for merged array

        while loc1 < len(left) and loc2 < len(right):
            #if the current array in the left half is smaller than the one in the right
            if left[loc1].title.strip().lower() <= right[loc2].title.strip().lower():
                sortedbooks[locM] = left[loc1] #put in the merged array
                loc1 += 1 # increment the pointer in the left half
            else:
                sortedbooks[locM] = right[loc2]#put in the merged arrary
                loc2 += 1 #increment the pointer in the right half
            locM += 1 #increment pointer in merged array
        #if there are any remaining add to merged array
        while loc1 < len(left):
            sortedbooks[locM] = left[loc1]
            locM += 1
            loc1 += 1
        while loc2 < len(right):
            sortedbooks[locM] = right[loc2]
            loc2 += 1
            locM += 1
            
    def merge_sort(self,sortedbooks, low, high):
        if high > low:
            mid = (low + high) // 2
            #post order
            self.merge_sort(sortedbooks, low, mid,)#sort left half recursively
            self.merge_sort(sortedbooks, mid + 1, high,) #sort right half recursively
            self.merge(sortedbooks, low, mid, high)#combine both halves
        return sortedbooks

    def loan_book(self, book_id, member_id):
        cursor = self.conn.cursor()
        #SQL query to see whether the book is out on loan
        cursor.execute('''SELECT checked_in FROM books WHERE id = ?''', (book_id,))
        book = cursor.fetchone()
        #the user has entered an incorrect book id, the book is not in the database
        if book == None:
            return "You have entered an incorrect Book ID."
        #if the checked in field is 0/False, then the book is currently on loan
        if book[0] == 0:
            return "This book is currently out on loan."
        
        loan_date = datetime.today().strftime("%d-%m-%Y") # the loan date, today
        due_date = (datetime.today() + timedelta(days=14)).strftime("%d-%m-%Y") # 14 days from loan date

        cursor.execute('''INSERT INTO loans (book_id, member_id, loan_date, due_date) VALUES (?, ?, ?, ?)''',
            (book_id, member_id, loan_date, due_date)) 
        # adds the book, member, loan date and due date in the loans table
        cursor.execute('''UPDATE books SET checked_in = 0 WHERE id = ?''', (book_id,)) #change book to loaned out
        self.conn.commit()
        return "You have successfully loaned out a book, your loan is due on {}.".format(due_date)

    def return_book(self, book_id): #Function to return a loaned book
        cursor = self.conn.cursor()
        cursor.execute('''UPDATE loans SET returned = 1 WHERE book_id = ? AND returned = 0''', (book_id,))
        #if not found in the loans database or has been returned already
        if cursor.rowcount == 0: 
            return "This book is not currently loaned out."
        else:
            #change loan returned field to 1/True
            cursor.execute('''UPDATE books SET checked_in = 1 WHERE id = ?''', (book_id,)) #change book to returned
            self.conn.commit()
            return "You have successfully returned the book with Book ID {}".format(book_id)
        
    def get_member_loans(self, member_id):#get a log of all the user's loans, (current and previous)
        cursor = self.conn.cursor()
        #return the id of the book, its title, its author, the due date and whether it has been returned
        #join both the loans and books table, with the book id as the foreign key
        cursor.execute('''SELECT books.id, books.title, books.author, loans.due_date, loans.returned
                     FROM loans
                     JOIN books ON loans.book_id = books.id
                     WHERE loans.member_id = ?''', (member_id,))
        loans = cursor.fetchall()
        return loans
        
class LibraryApp:
    def __init__(self, root, role):
        #starts both the book and member managers
        self.member_manager = MemberManager('members2.db') 
        self.book_manager = BookManager('books2.db')  

        self.root = root# contains the Tkinter root window

        self.role = role  #store role of the logged in user

        self.root.title("Library Management System")
        self.is_high_contrast = False #Boolean value to check whether the user is using the high visibility mode or not (initially not)
        self.frame = tk.Frame(self.root) #the main frame for all the UI widgets
        self.create_widgets()
            

    def create_widgets(self):  
        if self.role == 'librarian':  # will only show if on a librarian account
            self.frame.pack(padx=10, pady=10)
            tk.Label(self.frame, text="Library Management System", font=("Arial", 16)).grid(row=0, columnspan=2, pady=10)
            tk.Button(self.frame, text="Add Book", command=self.add_book).grid(row=1, column=0, padx=5, pady=5)
            tk.Button(self.frame, text="Delete Book", command=self.delete_book).grid(row=1, column=1, padx=5, pady=5)
            tk.Button(self.frame, text="Add Member", command=self.add_member).grid(row=4, column=0, padx=5, pady=5)
            tk.Button(self.frame, text="View Member Loans", command=self.view_member_loans).grid(row=5, column=0, padx=5, pady=5)
            tk.Button(self.frame, text="Delete Member", command=self.delete_member).grid(row=4, column=1, padx=5, pady=5)
            tk.Button(self.frame, text="Search Book by Title", command=self.search_book_by_title).grid(row=2, column=0, padx=5, pady=5)
            tk.Button(self.frame, text="Search Book by ISBN", command=self.search_book_by_isbn).grid(row=2, column=1, padx=5, pady=5)
            tk.Button(self.frame, text="Loan Book", command=self.loan_book).grid(row=3, column=0, padx=5, pady=5)
            tk.Button(self.frame, text="Return Book", command=self.return_book).grid(row=3, column=1, padx=5, pady=5)
            tk.Button(self.frame, text="Sort Books Alphabetically", command=self.sort_books_alphabetically_by_genre).grid(row=5, column=1, padx=5, pady=5)
            tk.Button(self.frame, text="Toggle High Visibility", command=self.toggle_high_contrast).grid(row=6, columnspan=2, padx=5, pady=5)
            tk.Button(self.frame, text="Exit", command=self.root.destroy).grid(row=7, columnspan=2, padx=5, pady=5)

        elif self.role == 'member':  # will only show if on a member account
            self.frame.pack(padx=10, pady=10)
            tk.Label(self.frame, text="Library Management System", font=("Arial", 16)).grid(row=0, columnspan=2, pady=10)
            tk.Button(self.frame, text="Search Book by Title", command=self.search_book_by_title).grid(row=1, column=0, padx=5, pady=5)
            tk.Button(self.frame, text="Search Book by ISBN", command=self.search_book_by_isbn).grid(row=1, column=1, padx=5, pady=5)
            tk.Button(self.frame, text="Loan Book", command=self.loan_book).grid(row=2, column=0, padx=5, pady=5)
            tk.Button(self.frame, text="Return Book", command=self.return_book).grid(row=2, column=1, padx=5, pady=5)
            tk.Button(self.frame, text="Sort Books Alphabetically", command=self.sort_books_alphabetically_by_genre).grid(row=3, column=0, padx=5, pady=5)
            tk.Button(self.frame, text="Toggle High Visibility", command=self.toggle_high_contrast).grid(row=3, column=1, columnspan=2, padx=5, pady=5)
            tk.Button(self.frame, text="Exit", command=self.root.destroy).grid(row=4, padx=5, pady=5)
    
    def add_member(self):
        def submit():
            username = name_entry.get().strip() #remove any whitespace
            email = email_entry.get().strip()     
            password = password_entry.get() 

            if username == "" or email =="":
                messagebox.showerror("Invalid Entry", "You need to enter an entry for all fields.")
            #regular expression, to validate whether an email address was entered
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
            #ensuring valid username and password
            if re.match(email_regex, email)==None:
                messagebox.showerror("Invalid Email", "You have entered an invalid email address.")
                return

            if len(password) < 8:  # make sure the password is at least 8 characters long
                messagebox.showerror("Weak Password", "Your password should be at least 8 characters long.")
                return

            #hash the entered password      
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

            # creates a new member class
            member = Member(username, email, hashed_password)

            # add the member to the database
            result = self.member_manager.add_member(member)
            messagebox.showinfo("Result", result)

            add_member_window.destroy()
        # create new window
        add_member_window = tk.Toplevel(self.root)
        add_member_window.title("Add Member")
        
        tk.Label(add_member_window, text="Username").grid(row=0, column=0, padx=5, pady=5)
        name_entry = tk.Entry(add_member_window)
        name_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(add_member_window, text="Email").grid(row=1, column=0, padx=5, pady=5)
        email_entry = tk.Entry(add_member_window)
        email_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(add_member_window, text="Password").grid(row=2, column=0, padx=5, pady=5)
        password_entry = tk.Entry(add_member_window, show="*")  
        password_entry.grid(row=2, column=1, padx=5, pady=5)

        tk.Button(add_member_window, text="Submit", command=submit).grid(row=3, columnspan=2, pady=10)

    def delete_member(self):
        # code for deleting memeber from member database using member ID
        def submit():
            try: member_id = int(member_id_entry.get())
            except ValueError:
                messagebox.showerror("Invalid Entry", "The member ID should be a number.")
                return
            result = self.member_manager.delete_member(member_id)
            messagebox.showinfo("Result", result)
            delete_member_window.destroy()

        delete_member_window = tk.Toplevel(self.root)
        delete_member_window.title("Delete Member")
        
        tk.Label(delete_member_window, text="Member ID").grid(row=0, column=0, padx=5, pady=5)
        member_id_entry = tk.Entry(delete_member_window)
        member_id_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Button(delete_member_window, text="Submit", command=submit).grid(row=1, columnspan=2, pady=10)

    def add_book(self):
        def submit():
            #takes in user entry
            title = title_entry.get()
            author = author_entry.get()
            genre = genre_entry.get()
            isbn = isbn_entry.get()
            if title=="" or author=="" or genre=="" or isbn=="":
                messagebox.showerror("Invalid Input", "You must enter entries for every field.")
                return
            #creates new book object
            book = Book(title, author, genre, isbn)
            #attempts to insert it into the database
            result = self.book_manager.add_book(book)
            messagebox.showinfo("Result", result)
            add_book_window.destroy()

        add_book_window = tk.Toplevel(self.root)
        add_book_window.title("Add Book")
        
        tk.Label(add_book_window, text="Title").grid(row=0, column=0, padx=5, pady=5)
        title_entry = tk.Entry(add_book_window)
        title_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(add_book_window, text="Author").grid(row=1, column=0, padx=5, pady=5)
        author_entry = tk.Entry(add_book_window)
        author_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(add_book_window, text="Genre").grid(row=2, column=0, padx=5, pady=5)
        genre_entry = tk.Entry(add_book_window)
        genre_entry.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(add_book_window, text="ISBN").grid(row=3, column=0, padx=5, pady=5)
        isbn_entry = tk.Entry(add_book_window)
        isbn_entry.grid(row=3, column=1, padx=5, pady=5)

        tk.Button(add_book_window, text="Submit", command=submit).grid(row=4, columnspan=2, pady=10)
    
    def delete_book(self):
        # function to delete book from database
        def submit():
            try: book_id = int(book_id_entry.get())
            except ValueError:
                #if the user did not enter an integer
                messagebox.showerror("Invalid Input", "Book ID must be a number.")
                return
            #calls delete book function in book manager to remove the book id from the database
            result = self.book_manager.delete_book(book_id)
            messagebox.showinfo("Result", result)
            delete_book_window.destroy()
            
        delete_book_window = tk.Toplevel(self.root)
        delete_book_window.title("Delete Book")
        
        tk.Label(delete_book_window, text="Book ID").grid(row=0, column=0, padx=5, pady=5)
        book_id_entry = tk.Entry(delete_book_window)
        book_id_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Button(delete_book_window, text="Submit", command=submit).grid(row=1, columnspan=2, pady=10)

    def search_book_by_title(self):
            # code to search for a book according to its title
        def submit():
            booktitle = title_entry.get()
            result.delete(1.0, tk.END)# clear old resutls
            #2d list containing filtered books
            filteredbooks = self.book_manager.search_book_by_title(booktitle)#find the book() using a sql like query, function from book manager
            if filteredbooks == []:#if book not found and so list is empty
                result.insert(tk.END, "No books found.")
            else:
                for i in range (len(filteredbooks)):
                    #checks the status of the current book
                    if filteredbooks[i][5]== 1:
                        status="Checked In"
                    else:
                        status = "Checked Out"
                    result.insert(tk.END, "ID: {}, Title: {}, Author: {}, Genre: {}, ISBN: {}, Status: {}\n"
                        .format(filteredbooks[i][0],filteredbooks[i][1],filteredbooks[i][2],filteredbooks[i][3],filteredbooks[i][4],status))
                    
        search_book_window = tk.Toplevel(self.root)
        search_book_window.title("Search Book by Title")
        
        tk.Label(search_book_window, text="Title").grid(row=0, column=0, padx=5, pady=5)
        title_entry = tk.Entry(search_book_window)
        title_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Button(search_book_window, text="Submit", command=submit).grid(row=1, columnspan=2, pady=10)
        
        result= tk.Text(search_book_window, width=60, height=15)
        result.grid(row=2, columnspan=2, padx=5, pady=5)

    def search_book_by_isbn(self):
        def submit():
            searched_isbn = isbn_entry.get()
            book = self.book_manager.binary_search(searched_isbn)
            result.delete(1.0, tk.END)
            if book == None:# if book is not found
               result.insert(tk.END, "No book found with that ISBN.")
            else:
                result.insert(tk.END, "Title: {}, Author: {}, Genre: {}, ISBN: {}\n"
                    .format(book.title,book.author,book.genre,book.isbn))

        
        search_book_window = tk.Toplevel(self.root)
        search_book_window.title("Search Book by ISBN")
        
        tk.Label(search_book_window, text="ISBN").grid(row=0, column=0, padx=5, pady=5)
        isbn_entry = tk.Entry(search_book_window)
        isbn_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Button(search_book_window, text="Submit", command=submit).grid(row=1, columnspan=2, pady=10)
        
        result = tk.Text(search_book_window, width=60, height=15)
        result.grid(row=2, columnspan=2, padx=5, pady=5)

    def sort_books_alphabetically_by_genre(self):
        def submit():
            genre = genre_entry.get().strip() 
            books = self.book_manager.fetch_all_books()# fetch the list of all books in the databse
            if genre != "":
                books=self.book_manager.sort_books_by_genre(genre)#filter for all books of that genre
            
            sortedbooks = self.book_manager.merge_sort(books,0, len(books)-1)#merge sort to get it into alphabetical order so it can be placed
            
            result.delete(1.0, tk.END)

            # if there are no books within that genre
            if  sortedbooks == []:
                result.insert(tk.END, "No books found of the genre {}.".format(genre))
            else:
                # print all of the books and its data in order
                for i in range (len(sortedbooks)):
                    result.insert(tk.END, "Title: {}, Author: {}, Genre: {}, ISBN: {}\n"
                        .format(sortedbooks[i].title, sortedbooks[i].author,sortedbooks[i].genre,sortedbooks[i].isbn))
        
        sort_books_window = tk.Toplevel(self.root)
        sort_books_window.title("Sort Books Alphabetically")

        tk.Label(sort_books_window, text="Genre").grid(row=0, column=0, padx=5, pady=5)
        genre_entry = tk.Entry(sort_books_window)
        genre_entry.grid(row=0, column=1, padx=5, pady=5)
        tk.Button(sort_books_window, text="Sort Books", command=submit).grid(row=3, column=0, columnspan=2, pady=10)
        
        #text widget for the results
        result = tk.Text(sort_books_window, width=60, height=15)
        result.grid(row=1, columnspan=2, padx=5, pady=5)

    def loan_book(self):
        # code/function for loaning a book
        def submit():
            try: book_id = book_id = int(book_id_entry.get())
            except ValueError:
                messagebox.showerror("Invalid Entry", "The book ID should be a number.")
                return
            try: member_id = int(member_id_entry.get())
            except ValueError:
                messagebox.showerror("Invalid Entry", "The member ID should be a number.")
                return
            
            is_valid_user= self.member_manager.get_member_by_id(member_id)
            if is_valid_user==None:
                messagebox.showerror("Invalid Input", "You have entered an inccorrect Member ID.")
                return
            result = self.book_manager.loan_book(book_id, member_id)
            messagebox.showinfo("Result", result)
            loan_book_window.destroy()
    
        loan_book_window = tk.Toplevel(self.root)
        loan_book_window.title("Loan Book")
        
        tk.Label(loan_book_window, text="Book ID").grid(row=0, column=0, padx=5, pady=5)
        book_id_entry = tk.Entry(loan_book_window)
        book_id_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(loan_book_window, text="Member ID").grid(row=1, column=0, padx=5, pady=5)
        member_id_entry = tk.Entry(loan_book_window)
        member_id_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Button(loan_book_window, text="Submit", command=submit).grid(row=2, columnspan=2, pady=10)
     
    def return_book(self):
        # function for returning a book
        def submit():
            try: book_id = int(book_id_entry.get())
            except ValueError:
                messagebox.showerror("Invalid Entry", "The book ID should be a number.")
                return
            result = self.book_manager.return_book(book_id)
            messagebox.showinfo("Result", result)
            return_book_window.destroy()
        
        return_book_window = tk.Toplevel(self.root)
        return_book_window.title("Return Book")
        
        tk.Label(return_book_window, text="Book ID").grid(row=0, column=0, padx=5, pady=5)
        book_id_entry = tk.Entry(return_book_window)
        book_id_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Button(return_book_window, text="Submit", command=submit).grid(row=1, columnspan=2, pady=10)

    def view_member_loans(self):#function to view all loans from one member
        def submit():
            try: member_id = int(member_id_entry.get())
            except ValueError:
                messagebox.showerror("Invalid Entry", "The Member ID should be a number.")
                return
            loans = self.book_manager.get_member_loans(member_id)
            result.delete(1.0, tk.END)
            if loans == []:#if the loans list is empty
                result.insert(tk.END, "There are no loans for this member.")
            else:
                for i in range(len(loans)):
                    #references the specific returned books field and gives a text indicator/ "status"
                    if loans[i][4] == 1:
                        status= "Returned"
                    else:
                        status = "Not Returned"
                    result.insert(tk.END, "Book ID: {}, Title: {}, Author: {}, Due Date: {}, Status: {}\n".
                                       format(loans[i][0], loans[i][1],loans[i][2],loans[i][3],status))
       
        view_loans_window = tk.Toplevel(self.root)
        view_loans_window.title("View Member Loans")
        
        tk.Label(view_loans_window, text="Member ID").grid(row=0, column=0, padx=5, pady=5)
        member_id_entry = tk.Entry(view_loans_window)
        member_id_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Button(view_loans_window, text="Submit", command=submit).grid(row=1, columnspan=2, pady=10)
        
        result = tk.Text(view_loans_window, width=60, height=15)
        result.grid(row=2, columnspan=2, padx=5, pady=5)

    def toggle_high_contrast(self):
        #swaps between high visibility/contrast theme and normal theme
        if self.is_high_contrast==True:
            self.disable_high_contrast()
            self.is_high_contrast=  False
        else:
            self.enable_high_contrast()
            self.is_high_contrast= True

    def enable_high_contrast(self):
        apply_high_contrast(self.root)
        self.root.configure(background="black")
        self.frame.configure(bg="black")
        
    def disable_high_contrast(self):
        apply_normal_contrast(self.root)
        self.root.configure(background="SystemButtonFace")
        self.frame.configure(bg="SystemButtonFace")

def open_library_app(role):
        #open the library app
        library_root = tk.Tk()
        app = LibraryApp(library_root, role)
        library_root.mainloop()

def apply_high_contrast(widget):
    #changes all items in the program to yellow text with a black background
    #Try to change the background to black and the text to yellow or skip as certain widgets do not support this
    try: widget.configure(bg="black", fg="yellow")
    except: pass
    try: widget.configure(insertbackground="yellow")
    except: pass
    #recursively apply this colour scheme to all widgets
    children=widget.winfo_children()
    for i in range (len(children)):
        apply_high_contrast(children[i])

def apply_normal_contrast(widget):
    #return all the items in the program to black text on white background
    try:widget.configure(bg="SystemButtonFace", fg="black")
    except: pass
    try: widget.configure(insertbackground="black")
    except: pass
    #recursively apply this colour scheme to all widgets
    children=widget.winfo_children()
    for i in range (len(children)):
        apply_normal_contrast(children[i])


root = tk.Tk()
root.title("Login Screen")
root.geometry("300x200")  

# username entry
label_username = tk.Label(root, text="Username:")
label_username.pack(padx=5, pady=5)
entered_username = tk.Entry(root)
entered_username.pack(padx=5, pady=5)

# password entry
label_password = tk.Label(root, text="Password:")
label_password.pack(padx= 5,pady=5)
entered_password = tk.Entry(root, show="*")  #show asterisks so you cant see the password
entered_password.pack(padx=5, pady=5)

#login button
login_button = tk.Button(root, text="Login", command=validate_login)
login_button.pack(pady=20)
#tkinter main loop
root.mainloop()



