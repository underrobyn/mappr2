from flask import url_for, request, redirect, flash
from flask_admin.contrib.sqla import ModelView as SQLAModelView
from flask_admin.contrib.pymongo import ModelView as MongoModelView
from flask_login import current_user
from mappr import flaskadmin, db, mongo
from wtforms import form, fields
from mappr.models import User, NodeLocation, Bookmark, Node, Sector, CellIdBlockList, MapFile, GalleryFile


class AdminView(SQLAModelView):
	column_exclude_list = ['password_hash', ]

	def is_accessible(self):
		if current_user.is_authenticated:
			if current_user.id:
				user = User.query.get(current_user.id)
				if user.account_type > 4 or current_user.id == 1:
					return True

		return False

	def inaccessible_callback(self, name, **kwargs):
		flash("You are not logged in as an administrator")
		return redirect(url_for('login', next=request.url))


class FileForm(form.Form):
	_uuid = fields.StringField('_uuid')
	questions = fields.StringField('questions')


class FileView(MongoModelView):
	column_list = ()
	column_sortable_list = ()
	column_searchable_list = ()

	form = FileForm

	def get_list(self, *args, **kwargs):
		count, data = super(FileView, self).get_list(*args, **kwargs)

		return count, data

	def create_form(self):
		return super(FileView, self).create_form()

	def edit_form(self, obj):
		return super(FileView, self).edit_form(obj)


flaskadmin.add_view(AdminView(User, db.session))
flaskadmin.add_view(AdminView(NodeLocation, db.session))
flaskadmin.add_view(AdminView(CellIdBlockList, db.session))
flaskadmin.add_view(AdminView(Bookmark, db.session))

flaskadmin.add_view(AdminView(Node, db.session, category='Base Data'))
flaskadmin.add_view(AdminView(Sector, db.session, category='Base Data'))

flaskadmin.add_view(AdminView(GalleryFile, db.session, category='Files'))
flaskadmin.add_view(AdminView(MapFile, db.session, category='Files'))
# flaskadmin.add_view(FileView(mongo.db['gallery_files'], category='Files'))
