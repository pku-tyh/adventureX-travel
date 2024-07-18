
import atexit
import threading

from flask import Flask, request, jsonify
from flask_cors import CORS

from content_build import gen_city_brief
from game_process import GameProcess

app = Flask(__name__)

game_process = GameProcess()
CORS(app)


# Example cleanup function
def cleanup():
    print("Cleaning up resources")
    # Here, ensure all your threads or other resources are cleaned up properly
    # for thread in threading.enumerate():
    #     if thread is not threading.main_thread():
    #         # Perform cleanup for each thread
    #         pass


# Register cleanup function to be called on exit
atexit.register(cleanup)


# 初始化数据库

# 创建新用户
@app.route('/new_user', methods=['GET'])
def new_user():
    new_id = game_process.new_user()
    return jsonify(new_id=new_id)


# 获取用户信息
@app.route('/info', methods=['GET'])
def get_info():
    userid = request.args.get('userid')
    game_status = game_process.get_user_info(userid)
    if game_status:
        return jsonify(game_status=game_status)
    else:
        return jsonify(error='User not found'), 404


def calculate_important_cities(userid, important_cities):
    print('大城市简介生成')
    # 生成关键城市的简略信息
    import_city_brief_information: dict = gen_city_brief([x['name'] for x in important_cities[1:-1]])
    # 保存
    print('大城市简介生成完成')
    game_process.update_key_city_brief_info(userid, import_city_brief_information)


@app.route('/build_road', methods=['GET'])
def build_road():
    userid = request.args.get('userid')
    from_location = request.args.get('from_location')
    if from_location:
        from_location = [float(x) for x in from_location.split(',')]
    to_location = request.args.get('to_location')
    if to_location:
        to_location = [float(x) for x in to_location.split(',')]
    road, important_cities = game_process.build_path(userid, from_location, to_location)
    thread = threading.Thread(target=calculate_important_cities, args=(userid, important_cities))
    thread.start()
    return jsonify(availiable=True if len(road) else False, road=road, map_pins=important_cities)


@app.route('/start', methods=['GET'])
def npc_start():
    userid = request.args.get('userid')
    # 好像确实调用这个就好了
    game_process.npc_continue(userid)

    # 开始计算信息内容
    thread = threading.Thread(target=game_process.generation_after_start, args=userid)
    thread.start()
    return jsonify()


# 获取地图钉信息
@app.route('/pin_info_brief', methods=['GET'])
async def pin_info_brief():
    userid = request.args.get('userid')
    location = request.args.get('location')
    location = [float(x) for x in location.split(',')]
    pin_info = {
        'name': 'Example Pin',
        'location': location,
        'image': 'https://i.pinimg.com/564x/07/1b/5a/071b5af8581aa8fe3b53e2d76dcdb264.jpg',
        'introduction': '南京市是首批国家历史文化名城，中华文明的重要发祥地，长期是中国南方的政治、经济、文化中心。南京在35~60万年前已有南京猿人在汤山生活。南京市是首批国家历史文化名城，中华文明的重要发祥地，长期是中国南方的政治。',
        "time_expected": 1000 * 2 * 60
    }
    pin_info = game_process.get_map_pin_info_brief(userid, location)
    if pin_info['introduction']:
        return jsonify(pin_info)
    else:
        return jsonify()


@app.route('/pin_info_detailed', methods=['GET'])
async def pin_info_detailed():
    userid = request.args.get('userid')
    location = request.args.get('location')
    location = [float(x) for x in location.split(',')]
    pin_info = {
        'name': 'Example Pin',
        'location': location,
        'data': [
            {
                'image_url': 'https://i.pinimg.com/564x/07/1b/5a/071b5af8581aa8fe3b53e2d76dcdb264.jpg',
                'info': '内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文'
            },
            {
                'image_url': 'https://i.pinimg.com/564x/f5/4d/0d/f54d0db4912a4749ad318cbe893dd7a7.jpg',
                'info': '内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文内容文'
            },
            {
                'image_url': 'https://i.pinimg.com/originals/56/a4/58/56a45858390e3726d2848d3efa696d6e.jpg',
                'info': '内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文'
            },
            {
                'image_url': 'https://i.pinimg.com/564x/5b/f7/e2/5bf7e2cf4f616825054ace31d18d7bae.jpg',
                'info': '内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容容文本内容文本内容文本内容文本内容文本内容文'
            },
            {
                'image_url': 'https://i.pinimg.com/564x/8e/4e/7b/8e4e7b00343511b265276b98d730f29a.jpg',
                'info': '内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本内容文本本内容文本内容文本内容文本内容文本内容文内容文本内容容文本内容文本内容文本内容文本内容文本内容文内容文本内容容文本内容文本内容文本内容文本内容文本内容文内容文本内容容文本内容文本内容文本内容文本内容文本内容文本内容文'
            }
        ]
    }

    pin_info = game_process.get_map_pin_info(userid, location)
    if len(pin_info['data']):
        return jsonify(pin_info)
    else:
        return jsonify()
    # 此处实现获取地图钉信息的逻辑
    # 假设我们从数据库中获取


#
# # Socket 连接
# @socketio.on('connect', namespace=game_process.socket_namespace)
# def handle_connect():
#     user_id = request.args.get('userid')
#     if user_id is not None:
#         print(f'Client {user_id} connected')
#         sid = user_id
#         game_process.connected_clients[user_id] = sid
#         join_room(sid, namespace=game_process.socket_namespace)
#
#
# @socketio.on('disconnect', namespace=game_process.socket_namespace)
# def handle_disconnect():
#     print('Client disconnected')
#     user_id = request.args.get('userid')
#     if user_id in game_process.connected_clients.keys():
#         leave_room(user_id, namespace=game_process.socket_namespace)
#         del game_process.connected_clients[user_id]
#
#
# @socketio.on('message', namespace=game_process.socket_namespace)
# def handle_message(message):
#     print('received message', message)
#     user_id = request.args.get('userid')
#     game_process.receive_message(user_id, message)
#     # TODO: 如果ok, 这里进行后续发送消息


# @socketio.on('read', namespace=game_process.socket_namespace)
# def handle_message_read():
#     print('received message read')
#     user_id = request.args.get('userid')
#     game_process.message_read(user_id)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8011)
