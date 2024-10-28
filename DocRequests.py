import os
import requests
import hashlib


class DocRequests:
    @staticmethod
    def get_session():
        payload = {
            "login": "Admin",
            "password": hashlib.md5(b"qwerty").hexdigest()
        }
        session_request = requests.post(
            "http://localhost:8080/api/v1/login",
            headers={"Content-Type": "application/json"},
            json=payload
        )
        print(session_request.json()["session"])
        return session_request.json()["session"]

    @staticmethod
    def get_template_ids(session_id):
        template_ids = requests.get(f"http://localhost:8080/api/v1/workspace"
                                    f"/templates?session={str(session_id)}")

        if template_ids.status_code != 200:
            raise Exception("failed to get template ids")

        return template_ids

    @staticmethod
    def fillDoc(file, session, passport_data):
        data_to_fill = '{"ID1":' + passport_data["Фамилия"] + ',' + \
                       '"ID2":' + passport_data["Имя"] + ',' + \
                       '"ID3":' + passport_data["Отчество"] + ',' + \
                       '"ID4":' + passport_data[
                           "Дата рождения"] + ',' + \
                       '"ID5":' + passport_data[
                           "Серия"] + ',' + \
                       '"ID6":' + passport_data[
                           "Номер"] + '}'
        print(data_to_fill)
        payload = {
            "file": file,
            "session": session,
            "data": data_to_fill
        }
        filled_doc = requests.post(
            "http://localhost:8080/api/v1/workspace/fillDocz",
            headers={"Content-Type": "application/json"},
            json=payload
        )
        return filled_doc

    @staticmethod
    def get_template_id(template_ids):
        return template_ids.json()["data"][0]["recordId"]

    @staticmethod
    def get_file_info(session, id):
        info = requests.get(f"http://localhost:8080/api/v1/workspace/file"
                            f"?session={session}&id={id}")
        return info

    @staticmethod
    def get_doc_id(session, file):
        return DocRequests.get_file_info(session, file). \
            json()["data"][0]["documentId"]

    @staticmethod
    def download_file(file, session, filename, content_type):
        try:
            document = DocRequests.get_doc_id(session, file)
        except:
            session = DocRequests.get_session()
            document = DocRequests.get_doc_id(session, file)
        print(document)
        payload = {
            "file": file,
            "session": session,
            "document": f"[{document}]",
            "contentType": content_type
        }
        print(file)
        response = requests.post("http://localhost:8080/api/v1/workspace/file",
                                 headers={"Content-Type": "application/json"},
                                 json=payload)

        doc_dir = os.path.join('user_documents')
        if not os.path.exists(doc_dir):
            os.makedirs(doc_dir)
        filepath = os.path.join(doc_dir, filename + "." + content_type)
        with open(filepath, 'wb') as file:
            file.write(response.content)
