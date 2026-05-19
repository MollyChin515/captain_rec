#先运行这个接收端，再运行发送端
import argparse
import json

from flask import Flask, request
import numpy as np
import cv2
import os

app = Flask(__name__)
# cv2.namedWindow('haha', 0)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files and 'data' not in request.form:
        return {'message': '没有文件被上传'}, 400
    image_field = request.files['file']
    image_buffer = image_field.read()
    image_array = np.asarray(bytearray(image_buffer), dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)[:, :, ::-1]
    # cv2.imshow('haha', image)
    # cv2.waitKey(1)

    current_dir = os.path.dirname(os.path.abspath(__file__))

    cv2.imwrite(current_dir + '/../uploads/' + image_field.filename.split('.')[0] + '.jpg', image)

    json_field = request.form["data"]
    json_data = json.loads(json_field)
    # 将JSON数据保存到文件
    with open(current_dir + '/../uploads/' + image_field.filename.split('.')[0] + '.json', 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)

    # data = json_field.get_json()
    # json_buffer = json_field.read()
    # json.load(json_field)

    # file = request.files['file']
    # file.save(f'./uploads/{file.filename}')
    return {'message': '文件上传成功', 'code': 200}, 200

def cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='示例：运行时传参模板')
    parser.add_argument('-p', '--port',  type=int, default=5008, help='端口号 (默认5008')
    return parser.parse_args()

if __name__ == '__main__':
    args = cli()
    app.run(host='127.0.0.1', port=args.port)