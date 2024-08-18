from abc import ABC, abstractmethod
import pickle
from collections import UserDict
from datetime import datetime, timedelta
from pathlib import Path

file_path = Path("database.bin")

# Опис базового класу для представлення
class UserInterface(ABC):
    @abstractmethod
    def display_message(self, message):
        pass

    @abstractmethod
    def get_input(self, prompt):
        pass

    @abstractmethod
    def display_contact(self, contact):
        pass

    @abstractmethod
    def display_all_contacts(self, contacts):
        pass

# Конкретна реалізація інтерфейсу для консольного застосунку
class ConsoleInterface(UserInterface):
    def display_message(self, message):
        print(message)

    def get_input(self, prompt):
        return input(prompt)

    def display_contact(self, contact):
        print(contact)

    def display_all_contacts(self, contacts):
        for contact in contacts:
            print(contact)

# Всі попередні класи, такі як Field, Name, Phone, Birthday, Record і AddressBook залишаються без змін
class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
    pass

class Phone(Field):
    def __init__(self, value):
        self.__value = None
        self.value = value

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        if len(value) == 10 and value.isdigit():
            self.__value = value
        else:
            raise ValueError("Invalid phone format")

class Birthday(Field):
    def __init__(self, value):
        date_format = "%d.%m.%Y"
        try:
            self.date = datetime.strptime(value, date_format).date()
            super().__init__(value)
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone_number):
        self.phones.append(Phone(phone_number))

    def remove_phone(self, phone_number):
        self.phones = [p for p in self.phones if str(p) != phone_number]

    def edit_phone(self, old_number, new_number):
        for phone in self.phones:
            if str(phone) == old_number:
                phone.value = new_number
                return
        raise ValueError("Phone number not found")

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}"

class AddressBook(UserDict):
    def add_record(self, record: Record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self, days=7) -> list:
        today = datetime.today().date()
        upcoming_birthdays = []

        for user in self.data.values():
            if user.birthday is None:
                continue
            birthday_this_year = user.birthday.date.replace(year=today.year)

            if birthday_this_year < today:
                birthday_this_year = birthday_this_year.replace(year=today.year + 1)

            if 0 <= (birthday_this_year - today).days <= days:
                upcoming_birthdays.append(
                    {
                        "name": user.name.value,
                        "congratulation_date": birthday_this_year.strftime("%Y.%m.%d"),
                    }
                )

        return upcoming_birthdays

def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return "Name not found. Please, check and try again."
        except ValueError as e:
            return e  # "Incorrect value. Please check and try again."
        except IndexError:
            return "Enter correct information."
    return inner

@input_error
def add_contact(args, book: AddressBook, ui: UserInterface):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    ui.display_message(message)

@input_error
def change_contact(args, book, ui: UserInterface):
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    if record:
        record.edit_phone(old_phone, new_phone)
        ui.display_message("Contact updated.")
    else:
        raise KeyError

@input_error
def show_phone(args, book, ui: UserInterface):
    (name,) = args
    record = book.find(name)
    if record:
        ui.display_message("; ".join([str(phone) for phone in record.phones]))
    else:
        raise KeyError

def show_all(book, ui: UserInterface):
    ui.display_all_contacts(book.data.values())

@input_error
def add_birthday(args, book, ui: UserInterface):
    name = args[0]
    birthday = args[1]
    record = book.find(name)
    if record:
        record.add_birthday(birthday)
        ui.display_message("Birthday added.")
    else:
        raise KeyError

@input_error
def show_birthday(args, book, ui: UserInterface):
    (name,) = args
    record = book.find(name)
    ui.display_message(str(record.birthday))

def load_data():
    if file_path.is_file():
        with open(file_path, "rb") as file:
            return pickle.load(file)
    else:
        return AddressBook()

def main():
    book = load_data()
    ui = ConsoleInterface()  # Створення інтерфейсу для консольного режиму
    ui.display_message("Welcome to the assistant bot!")

    while True:
        user_input = ui.get_input("Enter a command: ")
        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            ui.display_message("Good bye!")
            with open(file_path, "wb") as file:
                pickle.dump(book, file)
            break

        elif command == "hello":
            ui.display_message("How can I help you?")

        elif command == "add":
            add_contact(args, book, ui)

        elif command == "change":
            change_contact(args, book, ui)

        elif command == "phone":
            show_phone(args, book, ui)

        elif command == "all":
            show_all(book, ui)

        elif command == "add-birthday":
            add_birthday(args, book, ui)

        elif command == "show-birthday":
            show_birthday(args, book, ui)

        elif command == "birthdays":
            birthdays = book.get_upcoming_birthdays()
            if not len(birthdays):
                ui.display_message("There are no upcoming birthdays.")
                continue
            for day in birthdays:
                ui.display_message(f"{day}")

        else:
            ui.display_message("Invalid command.")

if __name__ == "__main__":
    main()
