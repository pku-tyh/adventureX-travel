import json
import sqlite3
import time

from flask_socketio import emit

from content_build import gen_city_brief, gen_small_point_content, generate_city_journey, gen_small_point_brief
from utils import haversine, get_route, sparse_route, current_timestamp, get_key_sights
import threading


class GameProcess:
    db_path = 'game.db'
    # 杭州的位置
    default_loc = [120.00799, 30.293316]
    npc_speed = 100.0
    game_speed = 6.0
    default_location_info_path = 'hangzhou.json'
    big_city_path = "big_city_loc.json"
    # 物理世界的十秒进行一次用户游戏状态的刷新
    fresh_interval = 5
    # userid:socket 连接映射
    connected_clients = {}
    socket_namespace = '/message'
    delta = 0.0001

    def __init__(self) -> None:
        with open(self.big_city_path, encoding='utf-8') as f:
            self.key_nodes = json.load(f)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        game_start_time INTEGER,
                        game_speed REAL,
                        npc_speed REAL,
                        npc_pending BOOLEAN,
                        random_index INTEGER
                    )''')
        c.execute('''CREATE TABLE IF NOT EXISTS npc_locations (
                        userid INTEGER PRIMARY KEY AUTOINCREMENT,
                        coord_lat REAL,
                        coord_lon REAL,
                        update_time INTEGER,
                        total_time INTEGER
                    )''')
        # 把地图针的介绍顺便放在
        c.execute('''CREATE TABLE IF NOT EXISTS map_pins (
                             id INTEGER PRIMARY KEY AUTOINCREMENT,
                             userid INTEGER,
                             coord_lat REAL,
                             coord_lon REAL,
                             name TEXT,
                             label TEXT,
                             introduction TEXT,
                             introduction_image_url TEXT
                         )''')

        # path of user
        c.execute('''CREATE TABLE IF NOT EXISTS user_path (
                             id INTEGER PRIMARY KEY AUTOINCREMENT,
                             userid INTEGER,
                             pointid INTEGER,
                             coord_lat REAL,
                             coord_lon REAL,
                             time_cost REAL
                         )''')
        # 消息序列
        c.execute('''CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        userid INTEGER,
                        role TEXT,
                        send_time INTEGER,
                        message TEXT,
                        coord_lat REAL,
                        coord_lon REAL,
                        image_url TEXT,
                        event TEXT,
                        read BOOLEAN
                    )''')

        # pins on map
        c.execute('''CREATE TABLE IF NOT EXISTS map_information (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        userid INTEGER,
                        coord_lat REAL,
                        coord_lon REAL,
                        image_url TEXT,
                        info TEXT
                    )''')
        conn.commit()
        conn.close()

    def game_time(self, game_start_time):
        real_time_elapsed = current_timestamp() - game_start_time
        return game_start_time + int(real_time_elapsed * self.game_speed)

    def new_user(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        # real time now
        game_start_time = int(time.time())
        # 基础表
        c.execute(
            'INSERT INTO users (game_start_time, game_speed, npc_speed,  npc_pending,random_index) VALUES (?, ?,  ?, ?,?)',
            (game_start_time, self.game_speed, self.npc_speed, True, 0))
        new_id = c.lastrowid

        c.execute(
            'INSERT INTO npc_locations (userid,coord_lat,coord_lon,update_time,total_time) VALUES (?, ?,  ?, ?,?)',
            (new_id, self.default_loc[0], self.default_loc[1], game_start_time, 0))

        conn.commit()
        conn.close()
        # 为用户提供第一个城市的信息
        self.initial_settings(new_id)
        return new_id

    def get_user_info(self, userid):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE id = ?', (userid,))
        user_data = c.fetchone()
        time_now = self.game_time(user_data[1])
        # 按照当前时间更新user_location
        user_location = self.calc_now_location(userid, time_now)

        map_pins, stage_total_time, stage_passed_time = self.get_all_map_pins(userid)
        if user_data:
            game_status = {
                'game_start_time': user_data[1],
                'game_speed': self.game_speed,
                'npc_speed': self.npc_speed,
                'npc_location': [user_location[0], user_location[1]],
                'map_pins': map_pins,
                'road': self.get_all_road(userid),
                'messages': self.get_message_available(userid),
                'time_now': time_now,
                'npc_pending': user_data[4],
                'stage_total_time': stage_total_time,
                'stage_passed_time': stage_passed_time
            }
            conn.close()
            return game_status
        else:
            conn.close()
            return None

    def save_road(self, userid, path):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        # time cost calculation: self.npc_speed m/s
        time_cost = 0
        path = [[x[0], x[1]] for x in path]
        for i in range(len(path)):
            if i == 0:
                time_cost = 0
            else:
                time_cost += int(haversine(path[i], path[i - 1]) * 1000 / self.npc_speed)
            c.execute(
                'INSERT INTO user_path (userid, pointid, coord_lat, coord_lon, time_cost) VALUES (?, ?, ?, ?, ?)',
                (userid, i, path[i][0], path[i][1], time_cost))
        conn.commit()
        conn.close()
        return path

    def get_all_road(self, userid):

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        # 执行查询
        c.execute('''SELECT * FROM user_path WHERE userid = ?''', (userid,))

        # 获取所有满足条件的记录
        records = c.fetchall()
        conn.commit()
        conn.close()
        res = [[x[3], x[4]] for x in records]
        return res

    def get_all_map_pins(self, userid):
        # 增加一些内容是包含
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        # 执行查询
        # 获取所有满足条件的记录
        c.execute('''SELECT * FROM  map_pins WHERE userid = ?''', (userid,))
        map_pins = c.fetchall()

        c.execute('SELECT * FROM npc_locations WHERE userid = ?', (userid,))
        npc_location = c.fetchone()
        conn.commit()
        conn.close()
        total_time = npc_location[4]

        # 检查是否完全通过等等
        passed = [self.check_map_pin_passed(userid, total_time, [x[2], x[3]]) for x in map_pins]
        stage_total_time = 0
        stage_passed_time = 0
        for i in range(1, len(passed)):
            # 因为地图钉在哪里
            if map_pins[i]['label'] == 'small':
                break
            if not passed[i][0]:
                stage_total_time = passed[i][1] - passed[i][0]
                stage_passed_time = total_time - passed[i][1]
                break
        res = [{
            'location': [x[2], x[3]],
            'name': x[4],
            'label': x[5],
            'passed': passed[i][0]
        } for i, x in enumerate(map_pins)]
        # 需要过滤没有通过的小地图钉
        res = [x for x in res if x['label'] == 'small' and not x['passed']]

        return res, stage_total_time, stage_passed_time

    def check_map_pin_passed(self, userid, total_time, location) -> tuple[bool, int]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # 地图钉一定在path 里面
        c.execute('''SELECT * FROM user_path WHERE userid=? AND coord_lat BETWEEN ? AND ?
           AND coord_lon BETWEEN ? AND ?''',
                  (userid, location[0] - self.delta, location[0] + self.delta, location[1] - self.delta,
                   location[1] + self.delta))
        point = c.fetchone()
        conn.commit()
        conn.close()
        if point[5] <= total_time:
            return True, point[5]
        else:
            return False, point[5]
        # 需要确定

    def append_map_pin(self, userid, location, label='small', name=''):
        # 加入地图钉，为了小的地点设置
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            'INSERT INTO map_pins (userid,  coord_lat, coord_lon, name, label,introduction,introduction_image_url) VALUES (?, ?, ?, ?, ?,?,?)',
            (userid, location[0], location[1], name, label, '', ''))
        conn.commit()
        conn.close()
        pass

    def save_map_pins(self, userid, path, map_pins):
        # 为了初始化设置
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        important_cities = [
            {
                'location': [x[1][0], x[1][1]],
                'name': x[0],
                'label': "big",
                'passed': False
            }
            for x in map_pins
        ]
        important_cities.insert(0, {'location': path[0], 'name': '', 'label': 'start', 'passed': True})
        important_cities.append({'location': path[-1], 'name': '', 'label': 'end', 'passed': False})

        # time cost calculation: self.npc_speed m/s

        for i in range(len(important_cities)):
            c.execute(
                'INSERT INTO map_pins (userid,  coord_lat, coord_lon, name, label,introduction,introduction_image_url) VALUES (?, ?, ?,?, ?,?,?)',
                (userid, important_cities[i]['location'][0], important_cities[i]['location'][1],
                 important_cities[i]['name'], important_cities[i]['label'], '', ''))
        conn.commit()
        conn.close()
        return important_cities

    def npc_pend(self, userid):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE id = ?', (userid,))
        user = c.fetchone()
        if user[4]:
            return
        else:
            time_now = self.game_time(user[1])
            self.calc_now_location(userid, time_now)
            c.execute("""
                  UPDATE users
                  SET npc_pending=?
                  WHERE id = ?
              """, (1, userid))
        conn.commit()
        conn.close()

    def npc_continue(self, userid):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE id = ?', (userid,))
        user = c.fetchone()
        time_now = self.game_time(user[1])
        self.calc_now_location(userid, time_now)

        if user[4]:
            c.execute("""
                               UPDATE users
                               SET npc_pending=?
                               WHERE id = ?
                           """, (0, userid))

        conn.commit()
        conn.close()
        # 开始 going on 了
        threading.Timer(self.fresh_interval, lambda x=userid: self.npc_going_on(x)).start()

    def npc_going_on(self, userid):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE id = ?', (userid,))
        user = c.fetchone()
        if user[4]:
            return
        # 每隔一段时间，看NPC什么状态，去想想办法
        c.execute('SELECT * FROM npc_locations WHERE userid = ?', (userid,))
        npc_location = c.fetchone()
        last_total_time = npc_location[4]
        conn.commit()
        # 检查是否有地图钉被新被接触
        # 小小地更新一次地点
        time_now = self.game_time(user[1])
        self.calc_now_location(userid, time_now)
        c.execute('SELECT * FROM npc_locations WHERE userid = ?', (userid,))
        new_total_time = npc_location[4]
        # 对于不同地图钉进行不同的消息传输
        c.execute('''SELECT * FROM  map_pins WHERE userid = ?''', (userid,))
        map_pins = c.fetchall()

        last_passed = [self.check_map_pin_passed(userid, last_total_time, [x[2], x[3]]) for x in map_pins]
        now_passed = [x[1] <= new_total_time for x in last_passed]
        last_passed = [x[0] for x in last_passed]

        conn.commit()
        for i in range(len(map_pins)):
            if now_passed[i] and not last_passed[i]:
                # 该停以及发消息了
                if map_pins[i][5] == 'small':
                    # 发送一条消息，但是不停
                    # message = {
                    #     'role': 'assistant',
                    #     'send_time': time_now,
                    #     'message': '',
                    #     'location': [map_pins[i][1], map_pins[i][2]],
                    #     'read': False,
                    #     'image_url': '',
                    #     'event': 'button_message'
                    # }
                    c.execute('''SELECT * FROM messages WHERE userid = ? AND coord_lat BETWEEN ? AND ?
                              AND coord_lon BETWEEN ? AND ?''',
                              (userid, map_pins[i][2] - self.delta, map_pins[i][2] + self.delta,
                               map_pins[i][3] - self.delta, map_pins[i][3] + self.delta))
                    message = c.fetchone()
                    if message is not None:
                        self.send_chat_message(userid, [map_pins[i][2], map_pins[i][3]])
                elif map_pins[i][5] in ['big', 'end']:
                    # 停止，并且发送一条消息
                    self.npc_pend(userid)
                    # message = {
                    #     'role': 'assistant',
                    #     'send_time': time_now,
                    #     'message': '',
                    #     'location': [map_pins[i][2], map_pins[i][3]],
                    #     'read': False,
                    #     'image_url': '',
                    #     'event': ''
                    # }
                    c.execute('''SELECT * FROM messages WHERE userid = ? AND coord_lat BETWEEN ? AND ?
                                                AND coord_lon BETWEEN ? AND ?''',
                              (userid, map_pins[i][2] - self.delta, map_pins[i][2] + self.delta,
                               map_pins[i][3] - self.delta, map_pins[i][3] + self.delta))
                    message = c.fetchone()
                    if message is not None:
                        self.send_chat_message(userid, [map_pins[i][2], map_pins[i][3]])

        print('新位置', userid, npc_location)
        conn.close()
        # 更新之后主动发送一次更新socket
        # self.send_notice_map(userid)
        # 重新开始
        threading.Timer(self.fresh_interval, lambda x=userid: self.npc_going_on(x)).start()

    def update_npc_location(self, userid: int, location: list[int], update_time: int, total_time: int):
        # 更新用户的位置
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
        UPDATE npc_locations
        SET coord_lat = ?, coord_lon = ?, update_time = ?, total_time = ?
        WHERE userid = ?
    """, (location[0], location[1], update_time, total_time, userid))
        conn.commit()
        conn.close()

    def calc_now_location(self, userid: int, time_now: int):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE id = ?', (userid,))
        user = c.fetchone()
        c.execute('SELECT * FROM npc_locations WHERE userid = ?', (userid,))
        npc_location = c.fetchone()
        if user[4]:
            # npc 此时没有移动
            self.update_npc_location(userid, [npc_location[1], npc_location[2]], time_now, npc_location[4])
            return [npc_location[1], npc_location[2]]

        time_delta = time_now - npc_location[3]
        time_total = npc_location[4] + time_delta
        c.execute(
            'SELECT * FROM user_path WHERE userid = ? AND time_cost <= ? ORDER BY time_cost DESC LIMIT 1',
            (userid, time_total))
        lower_point = c.fetchone()
        c.execute(
            'SELECT * FROM user_path WHERE userid = ? AND time_cost > ? ORDER BY time_cost LIMIT 1',
            (userid, time_total))
        upper_point = c.fetchone()
        conn.commit()
        conn.close()
        if lower_point is None:
            new_location = [upper_point[3], upper_point[4]]
        elif upper_point is None:
            new_location = [lower_point[3], lower_point[4]]
        else:
            time_cost = upper_point[5] - lower_point[5]
            t = time_total - lower_point[5]
            lat = lower_point[3] + (upper_point[3] - lower_point[3]) * t / time_cost
            lon = lower_point[4] + (upper_point[4] - lower_point[4]) * t / time_cost
            new_location = [lat, lon]
        self.update_npc_location(userid, new_location, time_now, time_total)

    def build_path(self, userid, start_coords, end_coords):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        # 查询就要删除所有老数据，以免数据不同步
        c.execute('DELETE FROM user_path WHERE userid = ?', (userid,))
        c.execute('DELETE FROM map_pins WHERE userid = ?', (userid,))
        # 提交更改
        conn.commit()
        self.append_map_pin(userid, self.default_loc, 'start', '杭州')
        c.execute('SELECT * FROM users WHERE id = ?', (userid,))
        user = c.fetchone()
        index = user[5]

        try:
            cached_city = {
                "江西省-景德镇市": (117.184576, 29.274248),
                "江苏省-南京市": (118.802422, 32.064653),
                "福建省-南平市": (118.0595, 27.292158)
            }
            cached_city_small = {
                "江苏省-南京市":[("太湖",(119.95806504147737,31.057889387825846)),("鸠兹古镇",(118.44411682166515,31.373892549849206))],
                "福建省-南平市":[("双龙洞",(119.67077825286448,29.188673613197395)),("云和梯田",( 119.49593495728658,28.052922830142673))],
                "江西省-景德镇市":[("千岛湖",( 118.98398445408088,29.65827277393035,)),("黄山",( 118.18185423864593,30.140280596779963))]
            }
            # which one is closer to end_coords
            min_distance = float('inf')
            min_location = None
            for city in cached_city:
                distance = haversine(cached_city[city], end_coords)
                if distance < min_distance:
                    min_distance = distance
                    min_location = city

            first_key_big = [(min_location, cached_city[min_location])]
            first_key_small = cached_city_small[min_location]
            first_key_all = first_key_small + first_key_big

            route_points = get_route(cached_city[min_location], end_coords)
            route_points = sparse_route(route_points, 25)
            key_all, key_big, key_small = self.choose_key_city(route_points, index)

            key_all = first_key_all + key_all
            key_big = first_key_big + key_big
            key_small = first_key_small + key_small
            # rebuild path by: start_coords -> key_city -> end_coords
            new_path = sparse_route(get_route(start_coords, key_all[0][1]), 25)

            for i in range(len(key_all) - 1):
                new_path += sparse_route(get_route(key_all[i][1], key_all[i + 1][1]), 25)[1:]

            new_path += sparse_route(get_route(key_all[-1][1], end_coords), 25)[1:]

            # 更新用户状态到数据库
            c.execute("""
                           UPDATE users
                           SET random_index = ?
                           WHERE id = ?
                       """, ((index + 1) % 5, userid))
            conn.commit()
            conn.close()
            # 更新路径与地图点
            new_path = self.save_road(userid, new_path)
            key_cities = self.save_map_pins(userid, new_path, key_big)
            # 直接把小点保存下来
            for point in key_small:
                self.append_map_pin(userid, point[1], name=point[0])
            return new_path, key_cities
        except Exception as e:
            print(e)
            conn.commit()
            conn.close()
            return [], []

    def calculate_distances(self, route):
        """
        计算所有关键节点到路径上最近节点的距离，并排序
        """
        distances = []

        for node_name, coord in self.key_nodes.items():
            min_distance = float('inf')
            min_location = None
            for route_point in route:
                distance = haversine(coord, route_point)
                if distance < min_distance:
                    min_distance = distance
                    min_location = route_point
            distances.append((node_name, min_distance, coord))
            # print(node_name,min_distance)

        distances.sort(key=lambda x: x[1])
        return distances

    def choose_key_city(self, route, index=2):
        index = index + 1
        line_distance = haversine(route[0], route[-1])
        n_choose = max(min(int(line_distance) // 300, 5), 1)
        distances = self.calculate_distances(route)
        possible_key_city = [distances[i] for i in range(n_choose * 5 + 2)][2:]
        distance_from_start = [haversine(route[0], city[2]) for city in possible_key_city]
        sorted_by_distance = sorted(zip(possible_key_city, distance_from_start), key=lambda x: x[1])

        # print(sorted_by_distance)
        province_last = {}
        cnt_province = {}

        return_keys = []
        for i in range(len(sorted_by_distance)):
            province = sorted_by_distance[i][0][0].split('-')[0]
            if province not in cnt_province:
                cnt_province[province] = 1
            else:
                cnt_province[province] += 1
            if cnt_province[province] == index:
                return_keys.append(sorted_by_distance[i][0][0])
            province_last[province] = sorted_by_distance[i][0][0]

        for province in cnt_province:
            if cnt_province[province] < index:
                return_keys.append(province_last[province])

        #  big
        sorted_return_keys = []
        small_points = []
        # all
        all_path_keys = []
        # small
        small_points_idx = []
        for i in range(len(sorted_by_distance)):
            if (sorted_by_distance[i][0][0] in return_keys):
                sorted_return_keys.append((sorted_by_distance[i][0][0], sorted_by_distance[i][0][2]))
                all_path_keys.append((sorted_by_distance[i][0][0], sorted_by_distance[i][0][2]))
            else:
                if len(small_points) < 5:
                    small_points.append((sorted_by_distance[i][0][0], sorted_by_distance[i][0][2]))
                    all_path_keys.append((sorted_by_distance[i][0][0], sorted_by_distance[i][0][2]))
                    small_points_idx.append(i)

        sights = get_key_sights([x[0].split('-')[-1] for x in small_points[:5]])

        for i, idx in enumerate(small_points_idx):
            if sights[i][1] is not None:
                all_path_keys[idx] = sights[i]
                small_points[i] = (sights[i][0], sights[i][1])

        # print(all_path_keys)
        # print(small_points)
        # print(sorted_return_keys)
        return all_path_keys, sorted_return_keys, small_points

    # def send_socket_message(self, userid, message_type, message):
    #     # 发送一条socket消息
    #     if userid in self.connected_clients.keys():
    #         emit(message_type, message, room=userid, namespace=self.socket_namespace)
    #     else:
    #         print(f'User {userid} not connected.')
    #
    # def send_notice_map(self, userid):
    #     self.send_socket_message(userid, 'notice_map', {})

    def save_chat_message(self, userid, message):
        # 提交插入操作
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
                 INSERT INTO messages (userid, role,send_time,message,coord_lat, coord_lon, image_url,event,read)
                 VALUES (?, ?, ?, ?, ?, ?,?,?,?)
                 ''', (userid, message['role'], message['send_time'], message['message'], message['location'][0],
                       message['location'][1], message['image_url'], message['event'], message['read']))
        conn.commit()
        conn.close()

    def get_message_available(self, userid):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT * FROM messages WHERE userid = ?', (userid,))
        messages = c.fetchall()
        res = []
        for message in messages:
            if message[3] > 0:
                res.append({
                    {
                        'role': message[2],
                        'send_time': message[3],
                        'message': message[4],
                        'location': [message[5], message[6]],
                        'read': message[9],
                        'image_url': message[7],
                        'event': message[8]
                    }
                })
        conn.commit()
        conn.close()
        return res

    def send_chat_message(self, userid, location):

        # 这里需要想想需要发送的东西是什么
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('SELECT * FROM users WHERE id = ?', (userid,))
        user = c.fetchone()
        # message['read'] = False
        # message['role'] = 'assistant'
        # message['send_time'] = self.game_time(user[1])
        c.execute('''UPDATE messages 
                     SET send_time = ? 
                     WHERE userid = ? AND coord_lat = ? AND coord_lon = ?''',
                  (self.game_time(user[1]), userid, location[0], location[1]))
        # self.save_chat_message(userid, message)
        # 通过socket发送
        # self.send_socket_message(userid, 'message', message)

        conn.commit()
        conn.close()

    def get_message_history(self, userid):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''SELECT * FROM messages WHERE userid = ?''', (userid,))
        messages = c.fetchall()
        conn.commit()
        conn.close()
        messages = [
            {
                'role': x[2],
                'send_time': x[3],
                'message': x[4],
                'location': [x[5], x[6]],
                'read': x[9],
                'image_url': x[7],
                'event': x[8]
            }
            for x in messages
        ]
        return messages

    def receive_message(self, userid, message):
        message['read'] = True
        message['role'] = 'user'
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE id = ?', (userid,))
        user = c.fetchone()
        message['send_time'] = self.game_time(user[1])
        self.save_chat_message(userid, message)
        conn.commit()
        conn.close()

    def message_read(self, userid):
        # 所有过去的信息变成了已读信息
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
        UPDATE messages
        SET read= ?
        WHERE userid = ?
        ''', (1, userid))
        conn.commit()
        conn.close()

    def get_map_pin_info_brief(self, userid, location):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''SELECT * FROM map_pins WHERE userid = ? AND coord_lat BETWEEN ? AND ?
           AND coord_lon BETWEEN ? AND ?''',
                  (userid, location[0] - self.delta, location[0] + self.delta, location[1] - self.delta,
                   location[1] + self.delta))
        map_pin = c.fetchone()
        c.execute('SELECT * FROM npc_locations WHERE userid = ?', (userid,))
        npc_location = c.fetchone()
        total_time = npc_location[4]
        conn.commit()
        conn.close()
        passed, time_expected = self.check_map_pin_passed(userid, total_time, location)

        return {
            'name': map_pin[4],
            'location': [map_pin[2], map_pin[3]],
            'image': map_pin[7],
            'introduction': map_pin[6],
            'time_expected': 0 if passed else time_expected - total_time
        }

    def get_map_pin_info(self, userid, location):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''SELECT * FROM map_pins WHERE userid = ? AND coord_lat BETWEEN ? AND ?
           AND coord_lon BETWEEN ? AND ?''',
                  (userid, location[0] - self.delta, location[0] + self.delta, location[1] - self.delta,
                   location[1] + self.delta))
        map_pin = c.fetchone()
        if map_pin is None:
            print(f"{userid} location {location} not found")
            return {
                'name': '',
                'location': location,
                'data': []
            }
        c.execute('''SELECT * FROM map_information
    WHERE userid = ? AND coord_lat BETWEEN ? AND ?
           AND coord_lon BETWEEN ? AND ?''', (
            userid, location[0] - self.delta, location[0] + self.delta, location[1] - self.delta,
            location[1] + self.delta))
        info_list = c.fetchall()
        conn.commit()
        conn.close()
        data = []
        for info in info_list:
            data.append({
                'image_url': info[4],
                'info': info[5]
            })
        return {
            'name': map_pin[4],
            'location': [map_pin[2], map_pin[3]],
            'data': data
        }

    def update_key_city_brief_info(self, userid, city_info: dict):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        for city_name in city_info.keys():
            c.execute('''
           UPDATE map_pins
           SET introduction = ?, introduction_image_url = ?
           WHERE userid = ? AND name = ?
           ''', (city_info[city_name]['description'], city_info[city_name]['photo'], userid, city_name))
        conn.commit()
        conn.close()

    def initial_settings(self, userid):
        # 初始化杭州的信息
        self.append_map_pin(userid, self.default_loc, 'start', '杭州')
        with open(self.default_location_info_path, 'r', encoding='utf-8') as f:
            city_detailed_info = json.load(f)
        self.save_city_detailed_info(userid, self.default_loc, city_detailed_info)

    def save_city_detailed_info(self, userid, location, city_detailed_info):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        # 将城市的详细信息保存在数据库里面
        for key in city_detailed_info.keys():
            for aspect in city_detailed_info[key]['aspects']:
                c.execute('''
                                INSERT INTO map_information (userid, coord_lat, coord_lon, image_url, info)
                                VALUES (?, ?, ?, ?, ?)
                                ''',
                          (userid, location[0], location[1], aspect["photo"], aspect["description"]))
        conn.commit()
        conn.close()

    def save_small_detailed_info(self, userid, location, city_info):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        # 将城市的详细信息保存在数据库里面
        for i in range(len(city_info["photos"])):
            c.execute('''
                                        INSERT INTO map_information (userid, coord_lat, coord_lon, image_url, info)
                                        VALUES (?, ?, ?, ?, ?)
                                        ''',
                      (userid, location[0], location[1], city_info['photos'][i], city_info["content"]))
        conn.commit()
        conn.close()

    def generation_after_start(self, userid):
        # 在出发之后，对于多个内容进行生成
        print("开始后续生成", userid)

        # 小点brief
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
    SELECT * FROM map_pins
    WHERE userid = ? AND label = ?
''', (userid, 'small'))
        pins = c.fetchall()
        print(pins)
        # c.execute('''
        #     SELECT * FROM map_pins
        #     WHERE userid = ? AND label = ?
        # ''', (userid, 'start'))
        # pins.append(c.fetchone())
        # c.execute('''
        #     SELECT * FROM map_pins
        #     WHERE userid = ? AND label = ?
        # ''', (userid, 'end'))
        # pins.append(c.fetchone())
        # city_brief_information: dict = gen_city_brief([x[4] for x in pins])
        # self.update_key_city_brief_info(userid, city_brief_information)

        # 到了每点的消息

        # 每个点的detail 除了第一个
        # 首先是小点
        print('小点')
        for pin in pins:
            print(pin)
            city_info = gen_small_point_content(pin[4], debug=False)
            self.save_small_detailed_info(userid, [pin[2], pin[3]], city_info)
            message = gen_small_point_brief(pin[4], city_info['content'], city_info['photos'][0])
            message = {
                'role': 'assistant',
                'send_time': 0,
                'message': message["content"],
                'location': [pin[2], pin[3]],
                'image_url': message['photo'],
                'event': 'button_message',
                'read': False
            }
            self.save_chat_message(userid, message)
        # 然后是大点

        print('大点')
        c.execute('''
                 SELECT * FROM map_pins
                 WHERE userid = ? AND label = ?
             ''', (userid, 'big'))
        pins = c.fetchall()
        for pin in pins:
            print(pin)
            city_info = generate_city_journey(pin[4])
            self.save_city_detailed_info(userid, [pin[2], pin[3]], city_info)
            message = gen_small_point_brief(pin[4], pin[6], pin[7])
            message = {
                'role': 'assistant',
                'send_time': 0,
                'message': message["content"],
                'location': [pin[2], pin[3]],
                'image_url': message['photo'],
                'event': 'button_message',
                'read': False
            }
            self.save_chat_message(userid, message)
        print('生成完成', userid)


if __name__ == '__main__':
    # 示例使用
    game_process = GameProcess()
    start_coords = (90.00799, 40.293316)  # 起点坐标 (纬度, 经度)
    end_coords = (110.15769013219844, 44.60997340940966)  # 终点坐标 (纬度, 经度)
    user_id = game_process.new_user()
    new_path, key_cities = game_process.build_path(user_id, start_coords, end_coords)
    # print(new_path)
    # print(key_cities)
