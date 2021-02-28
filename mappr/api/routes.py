from flask import Blueprint, request, abort, jsonify
from flask_login import current_user, login_required
from sqlalchemy import text
from ..functions import resp
from ..models import db, Node, Sector, Bookmark, NodeLocation

api_bp = Blueprint("api_bp", __name__, template_folder="templates", url_prefix='/api')


required_arguments = {
	'map': ['time', 'rat', 'mcc', 'mnc', 'ne_lat', 'ne_lng', 'sw_lat', 'sw_lng', 'show_mls', 'show_mappr'],
	'history': ['mcc', 'mnc', 'node_id']
}


def check_request_args(user_args, args):
	for argument in args:
		if argument not in user_args:
			print(argument)
			return False

	return True


@api_bp.app_errorhandler(404)
@api_bp.app_errorhandler(405)
def _handle_api_error(ex):
	if request.path.startswith('/api/'):
		return resp({}, error='Unknown')
	else:
		return ex


@api_bp.route('/update-node', methods=['POST'])
@login_required
def api_update_node():
	user_id = current_user.id
	rat = request.form.get('rat')
	mcc = request.form.get('mcc')
	mnc = request.form.get('mnc')
	node_id = request.form.get('node_id')

	lat = float(request.form.get('lat'))
	lng = float(request.form.get('lng'))

	new_location = NodeLocation(user_id=user_id, mcc=mcc, mnc=mnc, node_id=node_id, lat=lat, lng=lng)
	db.session.add(new_location)
	db.session.commit()

	return resp({
		'node_id':node_id,
		'lat':lat,
		'lng':lng
	})


@api_bp.route('/lookup-history', methods=['GET'])
@login_required
def api_node_history():
	if not check_request_args(request.args, required_arguments['history']):
		return abort(400)

	mcc = request.args.get('mcc')
	mnc = request.args.get('mnc')
	node_id = request.args.get('node_id')

	history_query = NodeLocation.query.filter_by(
		mcc=mcc,
		mnc=mnc,
		node_id=node_id
	).all()

	history_list = [{
		'mcc': row.mcc,
		'mnc': row.mnc,
		'node_id': row.node_id,
		'user_id': row.user_id,
		'time': row.time_created,
		'lat': float(row.lat),
		'lng': float(row.lng),
	} for row in history_query]

	return resp(history_list)


@api_bp.route('/lookup-node', methods=['GET'])
@login_required
def api_lookup_node():
	mcc = request.args.get('mcc')
	mnc = request.args.get('mnc')
	node_id = request.args.get('node_id')

	if not node_id:
		return resp(error='No node_id specified')

	if not mnc:
		node_query = Node.query.filter_by(
			mcc=mcc,
			node_id=node_id
		).all()
	else:
		node_query = Node.query.filter_by(
			mcc=mcc,
			mnc=mnc,
			node_id=node_id
		).all()

	node_list = [{
		'mcc': row.mcc,
		'mnc': row.mnc,
		'node_id': row.node_id,
		'lat': float(row.lat),
		'lng': float(row.lng),
	} for row in node_query]

	return resp(node_list)


@api_bp.route('/map', methods=['GET'])
@login_required
def api_get_map_area():
	if not check_request_args(request.args, required_arguments['map']):
		return abort(400)

	rat = request.args.get('rat')
	mcc = request.args.get('mcc')
	mnc = request.args.get('mnc')

	ne_lat = float(request.args.get('ne_lat'))
	ne_lng = float(request.args.get('ne_lng'))
	sw_lat = float(request.args.get('sw_lat'))
	sw_lng = float(request.args.get('sw_lng'))

	if mnc != "0":
		node_query = db.session.query(Node).filter(
			Node.mcc == mcc,
			Node.mnc == mnc,
			Node.lat >= sw_lat,
			Node.lng >= sw_lng,
			Node.lat <= ne_lat,
			Node.lng <= ne_lng
		).all()
	else:
		node_query = db.session.query(Node).filter(
			Node.mcc == mcc,
			Node.lat >= sw_lat,
			Node.lng >= sw_lng,
			Node.lat <= ne_lat,
			Node.lng <= ne_lng
		).all()

	def get_sectors_for_node(mcc, mnc, node_id):
		sectors_query = db.session.query(Sector).filter(
			Sector.mcc == mcc,
			Sector.mnc == mnc,
			Sector.node_id == node_id
		).all()

		sect_dict = {}
		for row in sectors_query:
			sect_dict[row.sector_id] = [
				float(row.lat),
				float(row.lng),
				row.created,
				row.updated,
				row.pci
			]

		return sect_dict

	node_list = [{
		'mcc': row.mcc,
		'mnc': row.mnc,
		'node_id': row.node_id,
		'lat': float(row.lat),
		'lng': float(row.lng),
		'created': row.created,
		'updated': row.updated,
		'samples': row.samples,
		'sectors': get_sectors_for_node(row.mcc, row.mnc, row.node_id)
	} for row in node_query]

	return resp(node_list)


@api_bp.route('/get-mccs', methods=['GET'])
@login_required
def api_get_mnc_list():
	mnc_query = db.engine.execute(text('SELECT DISTINCT nodes.mcc, nodes.mnc FROM nodes'))
	mnc_list = [[row[0], row[1]] for row in mnc_query]
	return resp(mnc_list)


@api_bp.route('/get-sectors', methods=['GET'])
@login_required
def api_get_sector_list():
	mcc = request.args.get('mcc')

	if not mcc:
		resp({}, error='Cannot process this request')

	sector_query = db.engine.execute(text('SELECT DISTINCT(sector_id), mnc FROM sectors WHERE mnc in (SELECT DISTINCT(mnc) as mnc FROM sectors) ORDER BY mnc, sector_id'))

	results = {}
	for row in sector_query:
		if row[1] not in results:
			results[row[1]] = []
		results[row[1]].append(row[0])

	return resp(results)


@api_bp.route('/bookmark/create', methods=['POST'])
@login_required
def api_bookmark_create():
	user_id = current_user.id

	mcc = request.form.get('mcc')
	mnc = request.form.get('mnc')

	lat = float(request.form.get('lat'))
	lng = float(request.form.get('lng'))
	zoom = int(request.form.get('zoom'))

	comment = request.form.get('comment')

	new_bookmark = Bookmark(user_id=user_id, mcc=mcc, mnc=mnc, lat=lat, lng=lng, zoom=zoom, comment=comment)
	db.session.add(new_bookmark)
	db.session.commit()

	return resp({})


@api_bp.route('/bookmark/delete', methods=['POST'])
@login_required
def api_bookmark_remove():
	user_id = current_user.id

	mcc = request.form.get('mcc')
	mnc = request.form.get('mnc')
	id = request.form.get('id')

	bookmark_item = Bookmark.query.filter(
		id == id,
		user_id == user_id,
		mcc == mcc,
		mnc == mnc
	).one()

	if not bookmark_item:
		return resp({}, error=True, msg='Bookmark not found')

	db.session.delete(bookmark_item)
	db.session.commit()

	return resp({})


@api_bp.route('/bookmark/get', methods=['GET', 'POST'])
@login_required
def api_bookmark_get():
	user_id = current_user.id

	bookmark_query = Bookmark.query.filter_by(
		user_id=user_id
	).all()

	bookmark_list = [{
		'mcc': row.mcc,
		'mnc': row.mnc,
		'lat': float(row.lat),
		'lng': float(row.lng),
		'zoom': int(row.zoom),
		'comment': row.comment,
		'created': row.time_created,
		'id': row.id
	} for row in bookmark_query]

	return resp(bookmark_list)
