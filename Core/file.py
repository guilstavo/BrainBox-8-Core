import json

class Json:

    def __init__(self, fileName: str = "config.json"):
        self.fileName = fileName
        print(f'Init Json File {self.fileName}')

        with open(self.fileName, 'r') as file:
            self.file = file
            self.data = json.load(file)


    def save_to_file(self, key: str, value):
        # Update the in-memory data
        self.data[key] = value

        print(f'Updated data: {self.data} for key: {key} with value: {value} in {self.fileName}')

        # Save the updated data back to the file
        with open(self.fileName, 'w') as file:
            json.dump(self.data, file)
            print(f'Saved {key}: {value} to {self.fileName}')

class Html:

    fileName: str

    def __init__(self, fileName: str = "index.html"):
        self.fileName = fileName

        data = ""
        with open(self.fileName, "r") as f:
            while True:
                chunk = f.read(512)  # read 512 bytes at a time
                if not chunk:
                    break
                data += chunk
            self.data = data
