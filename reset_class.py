import json

# 读取data.json文件
data_file_path = 'data.json'
with open(data_file_path, 'r', encoding='utf-8') as file:
    data = json.load(file)

print(f'原始数据中的学生数量: {len(data.get("students", []))}')

# 将所有学生的class字段置为空
for student in data.get('students', []):
    print(f'重置学生 {student["name"]} 的班级信息')
    student['class'] = ''

print(f'重置后的学生数据: {[(s["name"], s["class"]) for s in data.get("students", [])]}')

# 写回文件
with open(data_file_path, 'w', encoding='utf-8') as file:
    json.dump(data, file, ensure_ascii=False, indent=4)

print('data.json 文件已更新，所有学生的class字段已置为空')