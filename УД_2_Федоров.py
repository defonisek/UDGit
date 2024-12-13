import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import pandas as pd
import json
import os


class Database:

    def __init__(self, master):
        self.master = master
        master.title("База данных студентов")
        self.db_file=None
        self.index={}
        self.create_widgets()

    def create_widgets(self):
        # Меню (верхнее)
        menubar = tk.Menu(self.master)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Создать БД", command=self.create_db)
        filemenu.add_command(label="Открыть БД", command=self.open_db)
        filemenu.add_command(label="Удалить БД", command=self.delete_db)
        filemenu.add_command(label="Очистить БД", command=self.clear_db)
        filemenu.add_command(label="Backup БД", command=self.backup_db)
        filemenu.add_command(label="Восстановить из Backup", command=self.restore_db)
        filemenu.add_separator()
        filemenu.add_command(label="Выход", command=self.master.quit)
        menubar.add_cascade(label="Файл", menu=filemenu)
        self.master.config(menu=menubar)


        # Кнопки
        self.add_button = ttk.Button(self.master, text="Добавить запись", command=self.add_record)
        self.add_button.grid(row=1, column=0, padx=5, pady=5)

        self.delete_button = ttk.Button(self.master, text="Удалить запись", command=self.delete_record)
        self.delete_button.grid(row=1, column=1, padx=5, pady=5)


        self.search_button = ttk.Button(self.master, text="Найти запись", command=self.search_records)
        self.search_button.grid(row=1, column=2, padx=5, pady=5)


        self.edit_button = ttk.Button(self.master, text="Редактировать запись", command=self.edit_record)
        self.edit_button.grid(row=1, column=3, padx=5, pady=5)


        # Таблица (для пользователя)
        self.tree = ttk.Treeview(self.master, columns=("ID", "Имя", "Факультет", "Курс", "Средний балл"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Имя", text="Имя")
        self.tree.heading("Факультет", text="Факультет")
        self.tree.heading("Курс", text="Курс")
        self.tree.heading("Средний балл", text="Средний балл")
        self.tree.grid(row=2, column=0, columnspan=4, padx=5, pady=5)

    def load_index(self):
        if self.db_file:
            index_file = self.db_file + ".index" # файл индекса находится рядом с файлом базы
            try:
                with open(index_file, 'r') as f:
                    self.index = json.load(f)
                    print("Index: ",self.index)
            except (FileNotFoundError, json.JSONDecodeError):  # если с индексом что-то не так, то мы его переделываем
                self.rebuild_index()

    def save_index(self):
        if self.db_file:
            index_file = self.db_file + ".index"
            with open(index_file, 'w') as f:
                json.dump(self.index, f)

    def load_record(self, record_id):
        if not self.db_file or record_id not in self.index:
            return None
        try:
            with open(self.db_file, 'rb') as f:
                f.seek(self.index[record_id])
                line_bytes = f.readline()
                line = line_bytes.decode('utf-8', errors='ignore').rstrip('\r\n')
                if line: # если json не пустой
                    return json.loads(line)
                return None
        except (IOError, OSError, json.JSONDecodeError) as e:
            print(f"Ошибка загрузки {record_id}: {e}")
            return None
        
    def save_record(self, record_id, record_data):
        self.load_index()
        if not self.db_file:
            return
        if record_id in self.index:
            self.rebuild_database_file(record_id, record_data)  # передать обновленный и перестроить базу
        else: # добавляем, если новая запись
            with open(self.db_file, 'ab') as f: 
                json_str = json.dumps(record_data, ensure_ascii=False) + '\n'
                f.write(json_str.encode('utf-8'))
                self.index[record_id] = f.tell() - len(json_str.encode('utf-8')) # считаем и записываем позицию
        self.save_index()
    
    def rebuild_index(self):
        self.index = {}
        if self.db_file and os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'rb') as f:
                    position = 0
                    while True:
                        line_bytes = f.readline()
                        if not line_bytes: 
                            break 
                        line = line_bytes.decode('utf-8').rstrip('\r\n') 
                        try:
                            record = json.loads(line)
                            record_id = str(record.get('id'))
                            if record_id:
                                self.index[record_id] = position
                        except json.JSONDecodeError:
                            print("Пропускаем некорректную JSON запись")
                        finally:
                            position += len(line_bytes) # инкремент в байтах независимо от исключения
            except Exception as e:
                print(f"Ошибка перестройки индекса: {e}")
        self.save_index()

    def create_db(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            self.db_file = file_path
            self.clear_table()
            self.index.clear() 
            # пустой файл
            with open(self.db_file, 'w') as f:
                pass
            self.rebuild_index()
            self.save_index()
            print(f"База данных создана: {self.db_file}")


    def save_data(self, data_to_save): # используется ли записи пустой информации при очистке базы
        if self.db_file:
            with open(self.db_file, 'w') as f:
                json.dump(data_to_save, f, indent=4)


    def open_db(self):
        file_path = filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            self.db_file = file_path
            self.clear_table()
            self.index.clear()
            self.rebuild_index()
            self.load_index() 
            self.refresh_table()
            print(f"База данных открыта: {self.db_file}")



    def delete_db(self):
        if self.db_file:
            if os.path.exists(self.db_file):
                os.remove(self.db_file)
                print(f"База удалена: {self.db_file}")
                self.db_file = None
                self.clear_table()
        else:
            print("Не открыт файл базы данных для удаления.")


    def clear_db(self):
        if self.db_file:
            self.save_data({})
            self.refresh_table()
            print("База данных очищена.")


    def backup_db(self):
        if self.db_file:
            backup_file = self.db_file[:-5] + "_backup.json"
            try:
                with open(self.db_file, 'rb') as source_file, open(backup_file, 'wb') as target_file:
                    target_file.write(source_file.read())        
                # бэкап индекса
                index_backup_file = self.db_file[:-5] + "_backup.json.index"
                try:
                    with open(self.db_file + ".index", "rb") as index_source, open(index_backup_file, "wb") as index_target:
                        index_target.write(index_source.read())
                except Exception as e:
                    print(f"Ошибка бэкапа индекса: {e}")
                print(f"Бэкап создан: {backup_file}")
            except Exception as e:
                print(f"Ошибка создания бэкапа: {e}")
        else:
            print("Не открыта база данных для бэкапа.")


    def restore_db(self):
        file_path = filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if file_path:
            try:
                # копируем выбранный json в файл
                with open(file_path, 'rb') as source_file, open(self.db_file, 'wb') as target_file:
                    target_file.write(source_file.read())
                # копируем индекс
                index_file_path = file_path + ".index"
                with open(index_file_path, 'rb') as index_source, open(self.db_file + ".index", 'wb') as index_target:
                    index_target.write(index_source.read())
                self.rebuild_index()
                self.refresh_table()
                print(f"База восстановлена из: {file_path}")
            except FileNotFoundError:
                print(f"Ошибка: Индекс-файл не найден: {index_file_path}")
            except (IOError, OSError) as e:
                print(f"Ошибка в восстановлении базы: {e}")


    def add_record(self):
        def add_to_db():
            try:
                id_val = str(int(id_entry.get()))
                name_val = name_entry.get()
                faculty_val = faculty_entry.get()
                course_val = int(course_entry.get())
                gpa_val = float(gpa_entry.get())
                if self.load_record(id_val): # есть ли уже такой id
                    error_label.config(text="Ошибка: такой ID уже есть.")
                    return
                record_data = {
                    "id": int(id_val),
                    "name": name_val,
                    "faculty": faculty_val,
                    "course": course_val,
                    "gpa": gpa_val,
                }
                self.save_record(id_val, record_data)
                self.refresh_table()
                add_window.destroy()
            except ValueError as e:
                error_label.config(text=f"Error: {e}")

        # GUI
        add_window = tk.Toplevel(self.master)
        add_window.title("Добавить запись")


        id_label = tk.Label(add_window, text="ID:")
        id_label.grid(row=0, column=0)
        id_entry = tk.Entry(add_window)
        id_entry.grid(row=0, column=1)

        name_label = tk.Label(add_window, text="Имя:")
        name_label.grid(row=1, column=0)
        name_entry = tk.Entry(add_window)
        name_entry.grid(row=1, column=1)


        faculty_label = tk.Label(add_window, text="Факультет:")
        faculty_label.grid(row=2, column=0)
        faculty_entry = tk.Entry(add_window)
        faculty_entry.grid(row=2, column=1)


        course_label = tk.Label(add_window, text="Курс:")
        course_label.grid(row=3, column=0)
        course_entry = tk.Entry(add_window)
        course_entry.grid(row=3, column=1)

        gpa_label = tk.Label(add_window, text="Средний балл:")
        gpa_label.grid(row=4, column=0)
        gpa_entry = tk.Entry(add_window)
        gpa_entry.grid(row=4, column=1)



        error_label = tk.Label(add_window, text="", fg="red")
        error_label.grid(row=5, column=0, columnspan=2)


        add_db_button = ttk.Button(add_window, text="Добавить", command=add_to_db)
        add_db_button.grid(row=6, column=0, columnspan=2)


    def delete_record(self):
        selected_item = self.tree.selection()
        if selected_item:
            item_id = str(self.tree.item(selected_item)['values'][0])
            self.load_index()
            if item_id in self.index: 
                del self.index[item_id]
                self.save_index()
                self.rebuild_database_file()
                self.refresh_table()
        
    def rebuild_database_file(self, updated_record_id=None, updated_record_data=None):
        temp_file = self.db_file + ".temp" # временный файл
        try:
            with open(temp_file, 'wb') as temp_f, open(self.db_file, 'rb') as f:
                for existing_record_id, position in self.index.items():
                    if updated_record_id and existing_record_id == updated_record_id:
                        json_str = json.dumps(updated_record_data, ensure_ascii=False) + '\n'
                        temp_f.write(json_str.encode('utf-8'))
                    else:
                        f.seek(position)  # seek читает байт
                        line_bytes = f.readline()
                        line = line_bytes.decode('utf-8', errors='ignore').rstrip('\r\n')
                        try:
                            record = json.loads(line)
                            if str(record.get('id')) != existing_record_id:
                                print(f"Пропускаем несовпавший id записи: Ожидал {existing_record_id}, но получил {record.get('id')}")
                                continue
                            json_str = json.dumps(record, ensure_ascii=False) + '\n' 
                            temp_f.write(json_str.encode('utf-8')) 
                        except json.JSONDecodeError:
                            print("Пропускаем некорректную JSON запись")
        except (IOError, OSError) as e:
            print(f"Ошибка перестройки файла: {e}")
            return
        os.replace(temp_file, self.db_file)  
        self.rebuild_index()  # перестраиваем индекс, чтобы он совпал
        self.save_index()
    
    def search_records(self):
        def perform_search():
            search_field = field_var.get()
            search_value = value_entry.get()
            results = []
            self.load_index() 
            try:
                if search_field == "ID":
                    search_value = str(int(search_value))
                    if search_value in self.index:
                        record = self.load_record(search_value)
                        if record:
                            results.append(tuple(record.values()))
                    else:
                        print(f"Нет записи с ID: {search_value}")
                elif search_field in ("Курс", "Средний балл"):
                    search_value = float(search_value) if search_field == "Средний балл" else int(search_value)
                #  Если не id...
                if search_field != "ID": 
                    for record_id in self.index:  
                        record = self.load_record(record_id)
                        if record:
                            if search_field == "Имя":
                                compare_value = record.get("name", "").lower()
                                search_value = search_value.lower()
                            elif search_field == "Факультет":
                                compare_value = record.get("faculty", "").lower()
                                search_value = search_value.lower()
                            elif search_field == "Курс":
                                compare_value = record.get("course")
                            elif search_field == "Средний балл":
                                compare_value = record.get("gpa")
                            else:
                                continue 
                        if compare_value == search_value:
                            results.append((int(record_id), record.get("name"), record.get("faculty"), record.get("course"), record.get("gpa")))
            except ValueError:
                error_label.config(text="Неверный формат ввода для выбранного поля.")
            except Exception as e:
                print(f"Ошибка во время поиска: {e}")
                error_label.config(text="Неожиданная ошибка.")
            self.clear_table() 
            for row in results: 
                self.tree.insert("", tk.END, values=row)
            search_window.destroy()  # закрыть окно поиска


        search_window = tk.Toplevel(self.master)
        search_window.title("Поиск записей")

        field_label = tk.Label(search_window, text="Поле для поиска:")
        field_label.grid(row=0, column=0)

        field_var = tk.StringVar(value="ID") 
        field_options = ["ID", "Имя", "Факультет", "Курс", "Средний балл"]
        field_dropdown = ttk.Combobox(search_window, textvariable=field_var, values=field_options)
        field_dropdown.grid(row=0, column=1)

        value_label = tk.Label(search_window, text="Значение:")
        value_label.grid(row=1, column=0)

        value_entry = tk.Entry(search_window)
        value_entry.grid(row=1, column=1)

        error_label = tk.Label(search_window, text="", fg="red")
        error_label.grid(row=2, column=0, columnspan=2)

        search_button = ttk.Button(search_window, text="Найти", command=perform_search)
        search_button.grid(row=3, column=0, columnspan=2)

    def edit_record(self):
        selected_item = self.tree.selection()
        if selected_item:
            item_data = self.tree.item(selected_item)['values']
            item_id = str(item_data[0]) 
            def update_record():
                record = self.load_record(item_id)
                if not record: 
                    error_label.config(text=f"Ошибка: запись с ID {item_id} не найдена.")
                    return
                try:
                    new_name = name_entry.get()
                    new_faculty = faculty_entry.get()
                    new_course = int(course_entry.get())
                    new_gpa = float(gpa_entry.get())
                    if not new_name:
                        raise ValueError("Имя не может быть пустым.")
                    record.update({  
                        "name": new_name,
                        "faculty": new_faculty,
                        "course": new_course,
                        "gpa": new_gpa,
                    })
                    self.save_record(item_id, record)
                    self.refresh_table()
                    edit_window.destroy()
                except ValueError as e:
                    error_label.config(text=f"Ошибка: {e}")

            edit_window = tk.Toplevel(self.master)
            edit_window.title("Редактировать запись")
            name_label = tk.Label(edit_window, text="Имя:")
            name_label.grid(row=0, column=0)
            name_entry = tk.Entry(edit_window)
            name_entry.insert(0, item_data[1])
            name_entry.grid(row=0, column=1)

            faculty_label = tk.Label(edit_window, text="Факультет:")
            faculty_label.grid(row=1, column=0)
            faculty_entry = tk.Entry(edit_window)
            faculty_entry.insert(0, item_data[2])
            faculty_entry.grid(row=1, column=1)


            course_label = tk.Label(edit_window, text="Курс:")
            course_label.grid(row=2, column=0)
            course_entry = tk.Entry(edit_window)
            course_entry.insert(0, item_data[3])
            course_entry.grid(row=2, column=1)



            gpa_label = tk.Label(edit_window, text="Средний балл:")
            gpa_label.grid(row=3, column=0)
            gpa_entry = tk.Entry(edit_window)
            gpa_entry.insert(0, item_data[4])
            gpa_entry.grid(row=3, column=1)


            error_label = tk.Label(edit_window, text="", fg="red")  
            error_label.grid(row=4, column=0, columnspan=2)

            update_button = ttk.Button(edit_window, text="Обновить", command=update_record)
            update_button.grid(row=5, column=0, columnspan=2)

    def refresh_table(self):
        self.clear_table()  
        if self.db_file:
            self.load_index()
            display_data = [] # список только для хранения данных на вывод пользователю!
            for record_id in self.index:
                record = self.load_record(record_id)
                print("Запись: ",record)
                if record:
                    display_data.append(tuple(record.values())) # добавляем записи в массив
            print("Данные: ",display_data)
            for row in display_data:
                self.tree.insert("", tk.END, values=row)
            display_data.clear()
            print("Таблица обновлена.")
        else:
            print("Нет базы или некорректный файл.")

    def clear_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

root = tk.Tk()
db = Database(root)
root.mainloop()