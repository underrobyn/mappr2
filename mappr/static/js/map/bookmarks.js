/*
	Allows users to manage their bookmarks
*/

let _bookmarks = {

	list: [],

	init: function () {
		_bookmarks.reloadUi();
		_bookmarks.assignEvents();
		console.log('[Bookmarks]-> Initialised');
	},

	assignEvents: function () {
		$("#bookmarks_reload").on("click enter", _bookmarks.getList);
		$("#bookmarks_new").on("click enter", _bookmarks.createBookmark);
	},

	reloadUi: function () {
		_bookmarks.getList(function (data) {
			$('#bookmarks_list').empty();

			if (data.status || data.error === true || !data.response || data.response.length === 0) {
				let txt = 'Unknown error';
				if (data.statusText) {
					txt = data.statusText;
				} else {
					txt = data.error === true ? data.msg : 'No bookmarks found'
				}

				$('#bookmarks_list').append(
					$('<tr/>').append(
						$('<td/>', {
							'colspan': 3
						}).text(txt)
					)
				);
				return;
			}

			data.response.forEach(function (point) {
				$('#bookmarks_list').append(
					$("<tr/>", {
						"tabindex": 0,
						"data-id": point.id,
						"data-rat": 'lte',
						"data-mcc": point.mcc,
						"data-mnc": point.mnc,
						"data-lat": point.lat,
						"data-lng": point.lng,
						"data-zoom": point.zoom,
					}).on("click enter", _bookmarks.goToBookmark).append(
						$("<td/>").text(point.mcc + ' ' + point.mnc),
						$("<td/>").text(point.comment),
						$("<td/>").text(point.created)
					)
				);
			});
		});
	},

	goToBookmark: function () {
		_app.mcc = $(this).data('mcc');
		_app.mnc = $(this).data('mnc');

		let lat = $(this).data("lat");
		let lng = $(this).data("lng");
		let zoom = $(this).data("zoom") || 16;

		_history.updateUrl();
		_map.setLocation(lat, lng, zoom);
	},

	createBookmark: function () {
		let comment = prompt('This will create a bookmark of the current map location.\nAdd a comment to your bookmark?', '');
		_bookmarks.add(comment);
	},

	deleteBookmark: function () {
		let conf = confirm('Are you sure you want to delete this bookmark?');

		if (!conf) {
			return;
		}

		let id = $(this).data('id');
		let mcc = $(this).data('mcc');
		let mnc = $(this).data('mnc');
		let rat = $(this).data('rat');

		_bookmarks.remove(id, rat, mcc, mnc);
	},

	add: function (comment = 'No comment') {
		let xyz = _map.getMapXyz();

		let postData = {
			'rat': _app.rat,
			'mcc': _app.mcc,
			'mnc': _app.mnc,

			'lat': xyz.lat,
			'lng': xyz.lng,
			'zoom': xyz.zoom,

			'comment': comment
		};

		$.post(_api.base + 'bookmark/create', postData).done(function (resp) {
			console.log(resp);
			_bookmarks.reloadUi();
		});
	},

	remove: function (removeId, rat, mcc, mnc) {
		let postData = {
			'rat': rat,
			'mcc': mcc,
			'mnc': mnc,
			'id': removeId
		};

		$.post(_api.base + 'bookmark/delete', postData).done(function (resp) {
			console.log(resp);
		});
	},

	getList: function (cb) {
		let getData = {
			'rat': _app.rat,
			'mcc': _app.mcc,
			'mnc': _app.mnc
		};

		$.get(_api.base + 'bookmark/get', getData).done(cb).fail(cb);
	}
};
