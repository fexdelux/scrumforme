# -*- coding: utf-8 -*-

"""Global objects and methods declaration.

Unvolatile data fits better here, than in a db table.
Some structures are immutable. Days of week, for example.

As well as methods used throughout your app.

Here is their sweet home.
"""

## Global functions

def g_current_page(url, classe, empty=''):
    """returns a class if you are on url. Otherwise returns empty."""

    if request.args(0):
        url_server = '%s/%s/%s' % (request.controller, request.function, request.args(0))
    else:
        url_server = '%s/%s' % (request.controller, request.function)

    if url == url_server:
        return classe
    else:
        return empty

def g_if_in_current_page(url, classe, anotherclass):
    """returns a class if you are on the page, else returns another class"""

    if request.args(0):
        url_server = '%s/%s/%s' % (request.controller, request.function, request.args(0))
    else:
        url_server = '%s/%s' % (request.controller, request.function)

    if url == url_server:
        return classe
    else:
        return anotherclass


def g_blank_check(item):
    """returns a empty string if item is empty."""
    if item:
        return item
    else:
        item=""
        return item


def g_blank_return_question(item):
    """returns a '?' string if item is empty."""
    if item:
        return item
    else:
        item="?"
        return item


def g_blank_fulldate_check(item):
    """returns a empty string if item is empty."""
    if item:
        return item.strftime("%d/%m/%Y")
    else:
        item=""
        return item


def g_blank_date_check(item):
	"""returns a empty string if item is empty."""
	if item:
		return item.strftime("%d/%m")
	else:
		item=""
		return item


def g_format_number(number):
    """returns the number formatted with 0 before the number if less than 10"""
    if number < 10:
        number = " %s" % number

    return number


def g_person_id():
    """returns the person_id of logged user"""
    user_relationship = db(db.user_relationship.auth_user_id==auth.user.id).select().first()
    person_id = user_relationship.person_id

    return person_id


class G_projects(object):
    """header projects"""

    def newProject(self):
        from datetime import datetime

        folder = 'static/uploads/'
        form = SQLFORM.factory(
            Field('name', label=T('Name'), requires=IS_NOT_EMPTY(error_message=T('The field name can not be empty!'))),
            Field('description', label= T('Description')),
            Field('url', label= 'Url'),
            Field('thumbnail', type='upload',
            uploadfolder='%s%s' % (request.folder,folder)),
            table_name='projects',
            submit_button=T('CREATE')
            )

        if form.accepts(request.vars):
            person = _get_person()
            person_id = person["person_id"]

            if form.vars.thumbnail:
                image_name = self.convertImage(form.vars.thumbnail,folder)
            else:
                image_name = None

            project_id = Project.insert(
                            created_by=person_id,
                            name=form.vars.name,
                            description=form.vars.description,
                            url=form.vars.url,
                            date_=datetime.now(),
                            thumbnail=image_name,
                            )
            Sharing.insert(project_id=project_id,
                           person_id=person_id,
                           role_id=2,
                           )
            redirect(URL(f="product_backlog",args=[project_id]))

        elif form.errors:
            response.flash = T('form has errors')

        return form

    def updateThumbnail(self):
        project_id = request.args(0)
        folder = 'static/uploads/'
        form_thumbnail = SQLFORM.factory(
            Field('thumbnail', type='upload',
            uploadfolder='%s%s' % (request.folder,folder)),
            table_name='update',
            )
        if form_thumbnail.process().accepted:
            import subprocess

            folder = 'static/uploads/'
            upload_folder = '%s%s' % (request.folder,folder)
            if form_thumbnail.vars.thumbnail:
                image_name = self.convertImage(form_thumbnail.vars.thumbnail,folder)
            else:
                redirect(URL(f='product_backlog', args=[project_id]))

            project_update = db(Project.id == project_id).select().first()
            subprocess.call('rm %s/%s' % (upload_folder, project_update.thumbnail), shell=True)


            db(Project.id == project_id).update(thumbnail=image_name)
            redirect(URL(f='product_backlog', args=[project_id]))

        elif form_thumbnail.errors:
            response.flash = T('form has errors')

        return form_thumbnail


    def convertImage(self,base64txt,folder):
        import os
        import base64

        arglen = len(base64txt)
        if arglen > 1:
            uploadfolder=os.path.join(request.folder,folder)
            b64file = open(uploadfolder+base64txt, 'rb').read()
            if b64file.startswith("data:image/png;base64,"):
                b64file = b64file[22:]
            imgData = base64.b64decode(b64file)
            file_name = os.path.splitext(base64txt)
            fname = file_name[0] + '.png'

            # write image on filesystem
            imgFile = open(uploadfolder+fname, 'wb')
            imgFile.write(imgData)
            os.remove(uploadfolder+base64txt)
            return fname
        else:
            return False

    def projects(self):


        user_relationship = db(db.user_relationship.auth_user_id==auth.user.id).select().first()
        person_id = user_relationship.person_id

        if request.args(0):
            project_id = int(request.args(0))
            limit_b = 5
            db(Project.id == project_id).update(position_dom=0)
        else:
            limit_b = 4

        all_projects = db( (Sharing.person_id == person_id) &
                        (Project.id == Sharing.project_id ) ).select(orderby=Project.position_dom, limitby=(0, limit_b))

        if request.args(0):
            for project in all_projects:
                if project["project"].id == project_id and project["project"].position_dom == 0:
                    break
                else:
                    if (project["project"].position_dom + 1) < len(all_projects):
                        value = project["project"].position_dom + 1
                    else:
                        value = project["project"].position_dom - 1

                    db(Project.id == project["project"].id).update(position_dom=value)
            all_projects = [f for f in all_projects if f["project"].id != project_id]

        return dict(all_projects=all_projects)
