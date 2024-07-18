import requests
import openai
import json
import re
import concurrent.futures
from PIL import Image
from multiprocessing import Pool
from io import BytesIO
import base64

openai.api_key = "===="
client = openai.OpenAI()
gpt_35 = "gpt-3.5-turbo"
gpt_4o = "gpt-4o"

gpt_version = gpt_4o

google_api_key = '===='
google_cse_id = '===='
google_cse_id_xhs = '===='


def google_image_search(api_key, cse_id, query, num_results=5):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': api_key,
        'cx': cse_id,
        'q': query,
        'searchType': 'image',
        'num': num_results
    }
    response = requests.get(url, params=params)
    response.raise_for_status()

    results = response.json()
    print(results)
    image_urls = [item['link'] for item in results['items']]
    return image_urls


def gen_general(location_name):
    prompt = f"""
    请你基于自己的知识，帮我总结{location_name}值得来旅游的4大原因，对于每一点，请首先使用一个不超过 6 个字的标题（来描述这个方面，而非某个具体的景点），然后对这个标题进行一段200 字左右的话的详细解释，并且告诉我应该配什么样的图（方便我在搜索引擎搜索，尽可能涵盖多个方面（例如：历史、文化、地理、美食、景点、艺术等）
    你应当以如下 Json 格式输出：""" + """
    {
    summary:"对于整个城市的总体概述，说明有很多丰富的可玩的地方"
    aspects:[{
        title:"标题",
        description:"具体描述",
        photo:"你认为需要的配图内容，10 个字以内短语描述"},...
        ]
    }
    """
    response = client.chat.completions.create(
        model=gpt_version,
        response_format={"type": "json_object"},
        max_tokens=4096,
        n=1,
        stop=None,
        temperature=0.5,
        messages=[{"role": "system", "content": prompt}],

    )
    gpt_resp = json.loads(response.choices[0].message.content)
    return gpt_resp


def gen_history(location_name):
    prompt = f"""
    请你基于自己的知识，帮我总结{location_name}的4～5 个历史文化要点，对于每一点，请首先使用一个不超过 6 个字的标题介绍一个当地独特的历史文化内容，然后对这个标题进行一段 400 字左右的话的详细解释，并且告诉我应该配什么样的图（方便我在搜索引擎搜索，注意需要具有当地特色），尽可能涵盖多个方面（例如：知名历史人物和本地的渊源、重要的古代历史事件（不包括近代史）、重要文化的起源、民族宗教、民俗活动等），这些要点最好不要有明显的共性，要点不能是某个单一景点（因为景点会在后面的部分介绍），务必保证你的信息是真实的""" + """
    你应当以如下 Json 格式输出：
    {
    summary:"对于历史文化部分的总体描述"
    aspects:[{
        title:"标题",
        description:"具体描述",
        photo:"你认为需要的配图内容，10 个字以内短语描述"
        }
    ]

    """
    response = client.chat.completions.create(
        model=gpt_version,
        response_format={"type": "json_object"},
        max_tokens=4096,
        n=1,
        stop=None,
        temperature=0.5,
        messages=[{"role": "system", "content": prompt}],

    )
    gpt_resp = json.loads(response.choices[0].message.content)
    return gpt_resp


def gen_geography(location_name):
    prompt = f"""
    你是一个地理爱好者，请向我介绍{location_name}的地形地貌特点，先写一个概述（大约 200 字），然后包括 3～4 个方面的每一条大约 300 字的具体介绍，并给我提供搜索图片用的关键词，例如“某某市 海岸线”/“某某市 山地”。注意你只需要描述最有特点的那些部分，大多数省市都有的特点不必描述，每部分标题需要有差异。你应当按照如下的 json 格式输出""" + """
    {
        summary: "这个城市的地理特点概述"
        aspects:[{
        title:"这一条的概述描述，不超过 7 个字",
        description:"这一条的具体描述",
        photo:"这一条应当搭配的图片关键词"
        }]
    }

    """
    response = client.chat.completions.create(
        model=gpt_version,
        response_format={"type": "json_object"},
        max_tokens=4096,
        n=1,
        stop=None,
        temperature=0.5,
        messages=[{"role": "system", "content": prompt}],

    )
    gpt_resp = json.loads(response.choices[0].message.content)
    return gpt_resp


def gen_sight(location_name):
    prompt = f"""你是{location_name}的知名导游，现在有游客来这里旅游，需要游览这里比较著名的景点，请从自然景观和人文景观两个方面，各找 3 个景点，一共 6 个，介绍给游客，每一个景点的介绍需要具体且详细，大约为 500 字。
    你需要在介绍中以第一人称描述，不仅要介绍这个景点，更要记录你去这里看见了什么有趣的东西以及感受，就像你的旅行游记，每一条内容是独立的。
    请按照如下JSON 格式输出：""" + """
    {
        general: "对于旅游景点的整体概述，说明自然景观和人文景观都很丰富"
        aspects:[{
        title:"景点名字，前 3 个为自然景观，后 3 个为人文景观",
        description:"这一景点的具体描述，多段话间用\\n\\n分隔"
        }]
    }
    """
    response = client.chat.completions.create(
        model=gpt_version,
        response_format={"type": "json_object"},
        max_tokens=4096,
        n=1,
        stop=None,
        temperature=0.5,
        messages=[{"role": "system", "content": prompt}],

    )
    gpt_resp = json.loads(response.choices[0].message.content)
    # add key photo same as sight
    for i in gpt_resp['aspects']:
        i['photo'] = i['title']
    return gpt_resp


def gen_food(location_name):
    prompt = f"""你是{location_name}的知名美食博主，现在需要你向游客介绍这里的美食，你需要首先概述这里的美食状况，然后向他们介绍这里的 4 种不同的美食。
    这些美食你都是吃过的，因此要富有真情实感的描述你的感受，并发自内心地推荐，内容要详细，1000 字以上，可以基于美食有所延伸，扩展到历史文化。
    请按照如下 JSON 格式输出：""" + """
    {
        summary: "对于美食的总体概述，说明这里的美食特色"
        aspects:[{
            title:"美食名字",
            description:"具体描述，多段话间用\\n\\n分隔"
        }]
    }
    """
    response = client.chat.completions.create(
        model=gpt_version,
        response_format={"type": "json_object"},
        max_tokens=4096,
        n=1,
        stop=None,
        temperature=0.5,
        messages=[{"role": "system", "content": prompt}],

    )
    gpt_resp = json.loads(response.choices[0].message.content)
    # add key photo same as sight
    for i in gpt_resp['aspects']:
        i['photo'] = i['title']
    return gpt_resp


# query = '夫妻肺片'
# results = google_image_search(google_api_key, google_cse_id, query)

def download_and_convert_image(url):
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    buffered = BytesIO()
    img.save(buffered, format="PNG")  # 确保图像被保存到内存
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_str


def choose_image(data):
    urls, keyword = data
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai.api_key}"
    }
    urls = urls[:5]
    content = [{"type": "text", "text": f"""以下是一些关于{keyword}的图片, 请选出其中最能作为{keyword}展示图片一张。
选择标准：不是宫格图，没有文字图层， {keyword}占据图片主要区域，美观
你的输出应该是JSON格式，包含以下关键字
choicen_index: int // 你选择的图片序号，从0开始
"""}]
    for i, url in enumerate(urls):
        # content.append({"type": "image_url", "image_url": {"url": url}})
        base64_image = download_and_convert_image(url)
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
        })
    payload = {
        "model": "gpt-4o",
        "response_format": {"type": "json_object"},
        "messages": [{"role": "user", "content": content}]
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    # print(response.json())

    gpt_resp = response.json()['choices'][0]['message']['content']
    # use the regex to extract the first digit
    result = re.findall(r'\d+', gpt_resp)[0]
    return [keyword, urls[min(max(int(result), 0), 4)]]


def get_possible_images(keywords, debug=None):
    # http://116.62.58.160:5000/search
    # Body(Raw Json): {"keywords":["key1","key2",...]}
    # Response: {"key1":["url1","url2",...],"key2":["url1","url2",...],...}
    if debug:
        results = debug
    else:
        url = "http://116.62.58.160:5000/search"
        params = {
            'keywords': keywords
        }
        response = requests.post(url, json=params)
        results = response.json()
        # print(results)

    tasks = [(results[key], key) for key in results]
    # print(tasks)
    num_processes = 4
    with Pool(processes=num_processes) as pool:
        images = {}
        for res in pool.imap_unordered(choose_image, tasks):
            keyword = res[0]
            result = res[1]
            images[keyword] = result

    return images


def generate_city_description(city_name):
    prompt = f"请为以下城市写一段介绍：{city_name}。要求为纯文本，仅一段话，主要介绍知名人文历史事件，不要涉及任何数据（如面积、人口等），不超过 200 字。"
    response = client.chat.completions.create(
        model=gpt_4o,
        temperature=0.5,
        messages=[
            {"role": "system", "content": prompt}
        ]
    )
    description = response.choices[0].message.content.strip()
    return [city_name, description.split('\n')[0]]


def gen_city_brief(city_name_list):
    # 这个函数给了每个城市的基础信息
    num_processes = 4
    with Pool(processes=num_processes) as pool:
        desc = {}
        for res in pool.imap_unordered(generate_city_description, city_name_list):
            city = res[0]
            result = res[1]
            desc[city] = result
    images = get_possible_images(city_name_list)
    ret = {}
    for city in city_name_list:
        ret[city] = {
            'description': desc[city],
            'photo': images[city]
        }
    return ret


def generate_city_journey(city_name):
    # call gen_general(),gen_history(),gen_geography(),gen_sight(),gen_food() parallelly
    # return the results
    cached_city = {
        "南京": "./cached/nanjing.json",
        "景德镇": "./cached/jingdezhen.json",
        "南平": "./cached/nanping.json"
    }
    # check if the city is cached
    for key in cached_city:
        if key in city_name:
            with open(cached_city[key], 'r') as f:
                return json.load(f)
                
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(gen_general, city_name): "gen_general",
            executor.submit(gen_history, city_name): "gen_history",
            executor.submit(gen_geography, city_name): "gen_geography",
            executor.submit(gen_sight, city_name): "gen_sight",
            executor.submit(gen_food, city_name): "gen_food"
        }

        results = {}
        for future in concurrent.futures.as_completed(futures):
            func_name = futures[future]
            try:
                result = future.result()
                results[func_name] = result
            except Exception as exc:
                results[func_name] = f"generated an exception: {exc}"

        # extract the photo from each result
        all_photo_keys = []
        for key in results:
            for aspect in results[key]['aspects']:
                aspect['photo'] = aspect['photo'].replace(" ", "")
                all_photo_keys.append(aspect['photo'])

        # print(all_photo_keys)
        images = get_possible_images(all_photo_keys)
        # print(images)
        for key in results:
            for aspect in results[key]['aspects']:
                aspect['photo'] = images[aspect['photo']]

    return results


def gen_small_point_content(point_name, debug=False):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai.api_key}"
    }
    if debug:
        response = {'西湖': [
            'http://sns-webpic-qc.xhscdn.com/202407181835/93387eac0032f0d2ed71ddc5f2c94d39/1040g2sg314lq6j5s6ka04a6op17os8fjr9tmbqg!nd_dft_wgth_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181836/7a914109b6a5dbb6b01908ac4566ec09/1040g008314bjn6oe6e1g49bo1kp8ifge8i6g33g!nd_dft_wgth_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181836/98982f62e77468abbbb73578fc03fbb5/1040g2sg314ja635tm87g5pa3cbs0hhpkop95e7o!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181836/9f7b01f65444d38bc12cd085dcb54ea3/1040g2sg313fgb27a007g5n6c5g35kbfvlpv7eeg!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181836/b3213b59f22fd7da32e10c9f916d714c/1040g2sg314cqbbjb6g7049fsclm7klfl39l1jjg!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181836/0434d487d4b88ba72fd7810b60432cfa/1040g0083150kabba1a504a5tott6sm6keaba308!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181836/4c3d0144bb11eb4020dde0062f5dea30/1040g2sg315ab78osha204at8hhutoqael408ra0!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181836/779f1d79f8cb3d3cf235d8e8652daa97/1040g008312peqcdfhm0g5ohsfc3k0hm3s7vhqsg!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181836/815bd1c44f626b59608a850cb4d78b04/1040g00830nfj8v0j6i0g5nlm3ug08h1qu0i1ut0!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181836/16844ba0d30924ccfb070f42f361a279/1040g2sg30vomsboo5o0g4bfqfougdldjiofeii8!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181836/8b5a38aa048750fd0537c04ce66fa249/1040g0083150cec5che0g44ktrtiv5n8hi6dvsv8!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181836/d52b17c48e68afb9e0faef5458065d4a/1040g008311btqjjb6a4g5neu6ie08s1klbjnr38!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181836/e92998cbff9350a5a77ec9a05a993e12/1040g0083158vbonkh40g5otii9s9gi60ghjs21g!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181836/23ebbd62041398df429a2916f8abdc54/1040g008312vvs638680g5oleqdbmd3i8vm5bj3g!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181836/73829ad741850909c0441be1fdecdf3d/1040g2sg315al09jlgud05n8qqdk5n12vfr66370!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181836/4a2f73093606af16c2303966565d9277/1040g008315agnjof0u0g5p5qh9556qbq8mcru4o!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181836/89f66268cc126cc3869372d68973b652/1040g2sg315amplm5gm7g48cte4jq9o7sfbvb5u0!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181836/b9c38cd932718b4f20baabe9a02490b5/1040g00831185k0ghmm0g4a3nig3be84sencs9ho!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181836/01f30a5cdfb473fe827a567657028051/1040g0083156n7s28hc0g5nba9vb099vt6d7pukg!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181836/fa257fffa15b068c44b374f50139d535/spectrum/1040g0k0315940iq8gq005p7pt63h4ntuvkbbkjg!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181919/72fcc3d493278631aa5d82ebeae22ef0/1040g2sg314lq6j5s6ka04a6op17os8fjr9tmbqg!nd_dft_wgth_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181919/187dc47f17efcefe7ba502cfabb33f00/1040g008314bjn6oe6e1g49bo1kp8ifge8i6g33g!nd_dft_wgth_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181919/7ee40a03b44b92cd6126f079732319af/spectrum/1040g0k0314muvmf06k005pjscjshoshkvlphj9g!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181919/1586488e1c6580263b9ce2cf48a0bd3f/1040g008314br7ph35u4g5o7ahos08qri9s1vis8!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181919/8113b2de7df35fc95902239c4ff9938f/1040g2sg314ja635tm87g5pa3cbs0hhpkop95e7o!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181919/f2c7976161e30c87065ae9464d02945d/1040g2sg313a3is4t7q5g5pgi7tngu1f4ovgn93g!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181919/6dfd38657fb1caa99ee36c055f092820/1040g2sg313fgb27a007g5n6c5g35kbfvlpv7eeg!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181919/597fe62ed88f2e46f3d5a923a3ea6464/1040g2sg314cqbbjb6g7049fsclm7klfl39l1jjg!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181919/e890f4a0fce78ef187d48704ab6ada45/1040g0083156nfhjg0s0g4a90am6fr4vs3bii3fo!nd_dft_wgth_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181919/377008bd65ccef29505ba5919b0e2880/1040g2sg31517e9nn147g40l14vbi49ks434k49g!nd_dft_wgth_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181919/4ae0edfa4f776fb586c0e9d4a0913ec1/1040g0083150kabba1a504a5tott6sm6keaba308!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181919/d3b3e7816c6aa5277610938722ea48a3/1040g008312peqcdfhm0g5ohsfc3k0hm3s7vhqsg!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181919/82abfb97187ec300efb5a9a8ee30f63c/1040g00830nfj8v0j6i0g5nlm3ug08h1qu0i1ut0!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181919/74d76613211aaca329388f5df9cbced7/1040g2sg30vomsboo5o0g4bfqfougdldjiofeii8!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181919/822cc22fcc518cfcfa9a491c76cab986/1040g0083150cec5che0g44ktrtiv5n8hi6dvsv8!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181919/863c3f76b8c444cdb5142778597dbf31/1040g008311btqjjb6a4g5neu6ie08s1klbjnr38!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181919/0847a242ec387549eddf60fecb2d758c/1040g2sg313b7pmrc04705o0grl1gbs873lh6vf0!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181919/df824bb136e6982fa8ea86a150ae31a5/1040g00831457t22h180g5pch30q8he8honu31bg!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181919/144c03f89e7bde4a8155e0c01df5a695/1040g0083158vbonkh40g5otii9s9gi60ghjs21g!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181919/e7967fe7c0c901b48febdfd764edeaa7/1040g008312vvs638680g5oleqdbmd3i8vm5bj3g!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407182008/7370190d124346dc34b75b58f7dd8ec1/1040g2sg314bqfrbjm2705o550gdgbrmfiaa49a0!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407182008/fb77dd0ff83c0db7485131e1586c5a8a/1040g2sg314lo8bogm87g5ni4raa092qp6m6e4l0!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407182008/2234f4b82c1d1ff3b4dd70003b81765e/1040g2sg314mbrech6e004bbvlp97tvffuvqeoq0!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407182008/22197c264f6c1adec3283c90760ac732/spectrum/1040g0k0314pg0opags005o39sl90bglah9vrec8!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407182008/6dbb0b2e0ccf4df182be71890b01f4c2/1040g2sg313pbbnquhm7g5pb9a7q73fv1m2fpa2o!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407182008/058591fe651bd7bfd1e7303d2857ce23/spectrum/1040g0k0312vseuad64005nqm72mg97nr8vcf7m8!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407182008/1fd6a4d9e91ef6948041727d3cde93c6/1040g2sg314n7j3lagg705ni4raa092qp665hk2g!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407182008/015159781de156159256cb8798bc391f/1040g2sg314cnfn28m2704a52qvndh8c9sut7ks8!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407182008/f4c09891af31a9fa7c81ea8375499d41/1040g008315467ihm0u2g5ntgqbdg84aomim04j8!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407182008/2ae94f20fc031b07badddd8e8791a0a6/1040g2sg314f30pgr5u7g5ntid8408b13itvsjcg!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407182008/ae735e6441a6bca61b14ece8ee366623/1040g008314bibv7d6g005ou98jdpic54mgva6bg!nd_dft_wgth_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407182008/cd5132f019329d553e7bf21906627135/1040g008314ctf2mb60004a6fo7ehhg54u03hboo!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407182008/89e362c8ab1217e59b7cb74a9123a0ac/1040g2sg314lq6j5s6ka04a6op17os8fjr9tmbqg!nd_dft_wgth_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407182008/b311b4a2d2651033951fd2811d08ee69/1040g008314cr1n1h6i004bg8lkps5suq5ujgioo!nd_dft_wgth_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407182008/b65347f5f1c42af05302587c7ca4d3a7/1040g008314bjn6oe6e1g49bo1kp8ifge8i6g33g!nd_dft_wgth_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407182008/953a9e5044cebef89242a8112be4b79d/1040g2sg313khqojsg0705nro6op088t6eqp4peo!nd_dft_wgth_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407182008/79e373360bd0ba0e654d7aa4edc6a242/1040g2sg314poc831gq7g498cfgspt5rl2t08vg0!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407182008/4858ed819c44cb1d8d54e1191dfef190/1040g2sg314m0mahb6i1g5om7u6o3hvujrsib7io!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407182008/80c79c9d1afc26e81579a74737cec92e/1040g008314klpscqmg0g5ofla6a40s7sj8vpvl8!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407182008/4f189947423217938adce9d114af6d63/1040g0083154u3gaghc0g4a7pva6o3nfi2rtm3b0!nd_dft_wlteh_webp_3']}
        urls = [
            'http://sns-webpic-qc.xhscdn.com/202407181835/93387eac0032f0d2ed71ddc5f2c94d39/1040g2sg314lq6j5s6ka04a6op17os8fjr9tmbqg!nd_dft_wgth_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181836/7a914109b6a5dbb6b01908ac4566ec09/1040g008314bjn6oe6e1g49bo1kp8ifge8i6g33g!nd_dft_wgth_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181836/0434d487d4b88ba72fd7810b60432cfa/1040g0083150kabba1a504a5tott6sm6keaba308!nd_dft_wlteh_webp_3']
    else:
        url = "http://116.62.58.160:5000/search"
        params = {
            'keywords': [point_name]
        }
        response = requests.post(url, json=params).json()
        urls = response[point_name][:7]

        content = [{"type": "text", "text": f"""以下是一些关于{point_name}的图片, 请选出其中最能作为{point_name}展示图片3张。
        选择标准：不是宫格图，没有文字图层， {point_name}占据图片主要区域，美观
        你的输出应该是JSON格式，包含以下关键字
        choicen_index: int // 你选择的图片序号，从0开始，如果有多张用逗号分隔
        """}]

        for i, url in enumerate(urls):
            # content.append({"type": "image_url", "image_url": {"url": url}})
            base64_image = download_and_convert_image(url)
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
            })
        payload = {
            "model": "gpt-4o",
            "response_format": {"type": "json_object"},
            "messages": [{"role": "user", "content": content}]
        }
        response_gpt = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        # print(response.json())

        gpt_resp = response_gpt.json()['choices'][0]['message']['content']
        # use the regex to extract the first digit
        print(gpt_resp)
        results = re.findall(r'\d+', gpt_resp)[:3]
        urls = [response[point_name][int(i)] for i in results]

    content = [{"type": "text",
                "text": f"""请你写一篇游记，来介绍{point_name}，主要描述你的感受，和看到了什么，然后推荐大家来玩，以下是你拍摄的该地图片，可以结合图片内容写，你是刚刚路过这个地方，并且迫不及待的把这篇文章分享给你最好的朋友，你这篇文章是为他一个人写的。"""}]
    print(urls)
    for i, url in enumerate(urls):
        # content.append({"type": "image_url", "image_url": {"url": url}})
        base64_image = download_and_convert_image(url)
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
        })
    payload = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": content}]
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    print(response.text)

    gpt_resp = response.json()['choices'][0]['message']['content']
    ret = {
        "content": gpt_resp,
        "photos": urls
    }
    return ret


def gen_small_point_brief(point_name, description, img_url):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai.api_key}"
    }
    content = [
        {"type": "text", "text": f"""请你基于以下的介绍，和这张图片，给你的朋友发送一条简短的消息，和他分享你在{point_name}的见闻和感受。
                这是一条微信消息，不要超过 70 字，只讲一件事即可，这张图会被一起发给朋友。介绍如下：
                {description}"""}]
    base64_image = download_and_convert_image(img_url)
    content.append({
        "type": "image_url",
        "image_url": {
            "url": f"data:image/jpeg;base64,{base64_image}"
        }
    })
    payload = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": content}]
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    gpt_resp = response.json()['choices'][0]['message']['content']
    ret = {
        "content": gpt_resp,
        "photo": img_url
    }
    return ret


if __name__ == '__main__':
    keywords = ["梅赛德斯奔驰中心", "中山陵", "马奶子"]
    test_data = {'北京烤鸭': [
        'http://sns-webpic-qc.xhscdn.com/202407181218/60a708d6f142cb1e43223c2e536b0ba6/1040g2sg30vn5q676600g4a0g8u3n44f3iek45q8!nd_dft_wlteh_webp_3',
        'http://sns-webpic-qc.xhscdn.com/202407181218/2056e42ff69a81f49537d4e890df3c0c/1040g00830osbi9b43m005o965p2g8f2hqdhsghg!nd_dft_wlteh_webp_3',
        'http://sns-webpic-qc.xhscdn.com/202407181218/f28d986dd6a4b629c98bf80c65da3447/1040g00830osbi9b43m0g5o965p2g8f2h9ia7c2o!nd_dft_wlteh_webp_3',
        'http://sns-webpic-qc.xhscdn.com/202407181218/e4e043ac6fc173ae20410b4f9a21a627/1040g00830osbi9b43m105o965p2g8f2heti2ul8!nd_dft_wlteh_webp_3',
        'http://sns-webpic-qc.xhscdn.com/202407181218/90ffceea51a663231b7cd6903f045241/1040g00830q0bgot7740049k84marbfof653dl88!nd_dft_wlteh_webp_3',
        'http://sns-webpic-qc.xhscdn.com/202407181218/98b3aeb7dadb4441b3bfe2c0aa1d3877/1040g00830q0bgot7740g49k84marbfof0tmh4jo!nd_dft_wlteh_webp_3',
        'http://sns-webpic-qc.xhscdn.com/202407181218/daf601cf776b2713a8ffda3230101442/1040g00830q0bgot7741049k84marbfofq5dm5dg!nd_dft_wlteh_webp_3',
        'http://sns-webpic-qc.xhscdn.com/202407181218/62672681300ccacea00bb71419ab8243/1040g2sg30v2gh9s1586g5odv09socf0525gaev8!nd_dft_wlteh_webp_3',
        'http://sns-webpic-qc.xhscdn.com/202407181218/a6497925fecd859abd5ed2768c9c3ff0/1040g00830v2gh9rfl6605odv09socf05fde3tg0!nd_dft_wlteh_webp_3',
        'http://sns-webpic-qc.xhscdn.com/202407181218/784d76d837dbf8daae54584519a6ddb2/1040g00830v2gh9ss545g5odv09socf05t8uuuug!nd_dft_wlteh_webp_3',
        'http://sns-webpic-qc.xhscdn.com/202407181218/527b5f6a687509bb0bd58ecdd4b248cf/1040g2sg3130r7lccmc705nsq5aq090os8cs2puo!nd_dft_wlteh_webp_3',
        'http://sns-webpic-qc.xhscdn.com/202407181218/595893079197c30b40f50df3f979bd26/1040g2sg3130r7lccmc7g5nsq5aq090ossr4tg78!nd_dft_wlteh_webp_3',
        'http://sns-webpic-qc.xhscdn.com/202407181218/edae767c85a910af83834df366cddc1d/1040g2sg3130r7lccmc805nsq5aq090osngo07a8!nd_dft_wlteh_webp_3'],
        '博雅塔': [
            'http://sns-webpic-qc.xhscdn.com/202407181219/ea3c1d16c6d0abcd1cda897bef9ec5a4/1040g00830mvrjqjgl6005ooge584hne8c0d1p4o!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181219/d13d394924a73a8a6f83a64db223f434/1040g2sg312bii6gh1m005nfpo7208j5dva0v42o!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181219/461c0dbe268e089d3dcd9c56faf3a430/1040g2sg312bii6gh1m0g5nfpo7208j5dk4ptfno!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181219/4b804c40f88f2a75c64b3855a224ed9b/1040g2sg312bii6gh1m4g5nfpo7208j5dtrpjr6o!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181219/b0be8ef483747a1147de4da1d843e5ab/1040g00830qjp33q102705noh1jvg8kv8ml1vus8!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181219/a1d161ad2200771e32e82960610a6a73/1040g00830qjp33q1027g5noh1jvg8kv81d9v6mg!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181219/a1bbab26b97741a00a936bfbb4d51a01/1040g00830qjp33q102805noh1jvg8kv8fh8t1bg!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181219/7509db5a0d9d3939de8e69ac87bfa587/1040g00830nbqdsse6i6g5nvpptj0bt723f3bn4g!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181219/57e1757543b9ab4f968ca17ca80bae6d/1040g00830nbqdsse6i605nvpptj0bt72m1161u0!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181219/b8b1c3e94039da16cf3dc6778e15c8d0/1040g00830nbqdsse6i5g5nvpptj0bt72l4l54v0!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181219/ea489dda6c3c2a266044751a0c6603ca/1040g008314kkk8acme0048po1ve2p6n1v0kiv80!nd_dft_wlteh_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181219/316ce56f614a30b63813265262dd333b/1040g008314kkk8acme0g48po1ve2p6n1tm1h4c0!nd_dft_wgth_webp_3',
            'http://sns-webpic-qc.xhscdn.com/202407181219/a6614a3974b06d32ef1a82e1b67d302b/1040g008314kkk8acme1048po1ve2p6n14jcfcg0!nd_dft_wgth_webp_3']}
    images = get_possible_images(keywords, test_data)

    print(images)

    city_name = "南京"
    description = generate_city_description(city_name)
    print(description)
    detail = generate_city_journey(city_name)
    print(detail)

    res = gen_city_brief(["南京市", "北京市", "成都市"])

    print(res)
