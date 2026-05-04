# aibls/views/gift_stat_route.py
from flask import request, jsonify, session, render_template
from aibls.decorators.decorator import check_session_go_login_decorator, check_session_2api_decorator
from aibls.services.gift_stat_service import gift_stat_service
from aibls.views import stat_api


@stat_api.route('/gift_stat')
@check_session_go_login_decorator
def gift_stat_page():
    """礼物统计页面"""
    login_user = session.get("login_user", {})
    return render_template('gift_stat.html',
                           nick_name=login_user.get("nick_name", "未登录"),
                           user_face=login_user.get("user_face", ""))


@stat_api.route('/api/months', methods=['GET'])
@check_session_2api_decorator
def get_available_months():
    """获取有数据的月份列表"""
    months = gift_stat_service.get_available_months()
    return jsonify({'code': 0, 'data': months})


@stat_api.route('/api/summary', methods=['GET'])
@check_session_2api_decorator
def get_monthly_summary():
    """获取月度汇总数据"""
    room_id = request.args.get('room_id', type=int)
    month = request.args.get('month')

    if not room_id:
        room_id = gift_stat_service.get_default_room()

    if not room_id:
        return jsonify({'code': -1, 'message': '未找到房间信息'})

    if not month:
        months = gift_stat_service.get_available_months()
        if months:
            month = months[0]
        else:
            return jsonify({'code': -1, 'message': '暂无数据'})

    summary = gift_stat_service.get_monthly_summary(room_id, month)
    if not summary:
        return jsonify({'code': -1, 'message': '获取数据失败'})

    return jsonify({'code': 0, 'data': summary})


@stat_api.route('/api/blind_boxes', methods=['GET'])
@check_session_2api_decorator
def get_blind_box_groups():
    """获取盲盒分组列表"""
    room_id = request.args.get('room_id', type=int)
    month = request.args.get('month')

    if not room_id:
        room_id = gift_stat_service.get_default_room()

    if not room_id:
        return jsonify({'code': -1, 'message': '未找到房间信息'})

    if not month:
        months = gift_stat_service.get_available_months()
        if months:
            month = months[0]
        else:
            return jsonify({'code': -1, 'message': '暂无数据'})

    data = gift_stat_service.get_blind_box_groups(room_id, month)
    return jsonify({'code': 0, 'data': data})


@stat_api.route('/api/user_rank', methods=['GET'])
@check_session_2api_decorator
def get_blind_box_user_rank():
    """获取盲盒用户投喂排名"""
    room_id = request.args.get('room_id', type=int)
    month = request.args.get('month')
    blind_gift_id = request.args.get('blind_gift_id', type=int)

    if not room_id:
        room_id = gift_stat_service.get_default_room()

    if not room_id:
        return jsonify({'code': -1, 'message': '未找到房间信息'})

    if not month:
        months = gift_stat_service.get_available_months()
        if months:
            month = months[0]
        else:
            return jsonify({'code': -1, 'message': '暂无数据'})

    if not blind_gift_id:
        return jsonify({'code': -1, 'message': '请选择盲盒'})

    data = gift_stat_service.get_blind_box_user_rank(room_id, month, blind_gift_id)
    return jsonify({'code': 0, 'data': data})