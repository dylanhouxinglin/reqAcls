import re

with open("./compare_page.210218_throw_exception", "r") as file:
    codes = file.read()

res = re.findall(r'data-title="models/service/page/acls/(.*).php"', codes)

with open("api_filenames", "w") as file:
    content = "\n".join([api for api in res])
    file.write(content)