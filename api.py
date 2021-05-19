from flask import Flask,request
import sqlite3 as sql 
from datetime import date,datetime
from flask_restplus import Api, Resource, fields
from werkzeug.contrib.fixers import ProxyFix
from functools import wraps

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

authorizations = {
    'apikey':{
        'type':'apiKey',
        'in' : 'header',
        'name': 'X-API-KEY'
    }
}
api = Api(app, version='1.0', title='TodoMVC API',
    description='A simple TodoMVC API',
    authorizations=authorizations
)

ns = api.namespace('todos', description='TODO operations')

todo = api.model('Todo', {
    'id': fields.Integer(readonly=True, description='The task unique identifier'),
    'task': fields.String(required=True, description='The task details'),
    'due_date': fields.String(required=True,description='The task last date to complete'),
    'cur_status': fields.String(required=True,default='Not Started',description='The task cur_status of completion')
})

# con = sql.connect('todo.db')
# con.execute('CREATE TABLE todos (id integer primary key, task TEXT, due_date TEXT, cur_status TEXT)')
# con.close()
def dict_from_row(row):
    return dict(zip(row.keys(), row))

def token_required(f):
    @wraps(f)
    def decorated(*args,**kwargs):
        token = None
        if 'X-API-KEY' in request.headers:
            token = request.headers['X-API-KEY']
        if not token:
            return {'message':'The Token is Required'},401
        if token != "prathyush":
            return {'message': 'The Token provided is not correct'},401
        return f(*args,**kwargs)
    return decorated

class TodoDAO(object):

    def getall(self):
        con=sql.connect('todo.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('SELECT * FROM todos')
        rows = cur.fetchall()
        con.close()
        return rows

    def get(self, id):
        todos = self.getall()
        for todo in todos:
            todo = dict_from_row(todo)
            if todo['id'] == id:
                return todo
        api.abort(404, "Todo {} doesn't exist".format(id))

    def create(self, data):
        todo = data
        all = self.getall()
        for each in all:
            id=each[0]
        todo['id'] = id+1
        with sql.connect("todo.db") as con:
            cur = con.cursor()
            cur.execute("INSERT INTO todos (id,task,due_date,cur_status) VALUES (?,?,?,?)",(todo['id'],todo['task'],todo['due_date'],todo['cur_status']) )
            con.commit()
        con.close()
        return todo

    def update(self, id, data):
        with sql.connect("todo.db") as con:
            cur = con.cursor()
            cur.execute("select * from todos where id = :id",{'id':id})
            ids=cur.fetchone()
            cur.close()
        con.close()
        if ids is not None:
            with sql.connect("todo.db") as con:
                cur = con.cursor()
                data['id']=id
                cur.execute("UPDATE todos SET task=:task ,due_date=:due_date ,cur_status=:cur_status WHERE id=:id",data)
                #{'task':todo['task'],'due':todo['due_date'],'stat':todo['cur_status'],'id':id}
                con.commit()
            con.close()
            return self.get(id)
        api.abort(404, "Todo with this ID doesn't exist")

    def getoverdue(self):
        today = datetime.today()
        arr=[]
        todos = self.getall()
        for todo in todos:
            todo = dict_from_row(todo)
            if datetime.strptime(todo['due_date'],'%Y-%m-%d') < today and todo['cur_status'] != "Finished":
                arr.append(todo)
        if arr:
            return arr
        api.abort(404, "Overdue Todo doesn't exist")

    def delete(self, id):
        with sql.connect("todo.db") as con:
            cur = con.cursor()
            cur.execute("select * from todos where id = :id",{'id':id})
            ids=cur.fetchone()
            cur.close()
        con.close()
        if ids is not None:
            with sql.connect("todo.db") as con:
                cur = con.cursor()
                cur.execute("DELETE from todos where id = :id",{'id':id})
                con.commit()
            con.close()
            return
        api.abort(404, "Todo with this ID doesn't exist")

    def updatestatus(self, id,cur_status):
        with sql.connect("todo.db") as con:
            cur = con.cursor()
            cur.execute("select * from todos where id = :id",{'id':id})
            ids=cur.fetchone()
            cur.close()
        con.close()
        if ids is not None:
            with sql.connect("todo.db") as con:
                cur = con.cursor()
                cur.execute("UPDATE todos SET cur_status=:stat WHERE id=:id",{'stat':cur_status,'id':id})
                con.commit()
            con.close()
            return self.get(id)
        api.abort(404, "Todo with this ID doesn't exist")

    def getfinished(self):
        arr=[]
        todos = self.getall()
        for todo in todos:
            todo = dict_from_row(todo)
            if todo['cur_status'] == "Finished":
                arr.append(todo)
        if arr:
            return arr
        api.abort(404, "Completed Todos doesn't exist")

    def getdue(self,date):
        arr=[]
        todos = self.getall()
        for todo in todos:
            todo = dict_from_row(todo)
            if todo['due_date'] == date and not todo['cur_status'] == "Finished":
                arr.append(todo)
        if arr:
            return arr
        api.abort(404, "Due Todos on this date doesn't exist")



DAO = TodoDAO()
# DAO.create({'task': 'Build an API','due_date': '2021-06-22','cur_status':'Not Started'})
# DAO.create({'task': '?????','due_date': '2021-05-17','cur_status':'Not Started'})
# DAO.create({'task': 'profit!','due_date': '2021-04-18','cur_status':'Not Started'})


@ns.route('/')
class TodoList(Resource):
    '''Shows a list of all todos, and lets you POST to add new tasks'''
    @ns.doc('list_todos')
    @ns.marshal_list_with(todo)
    def get(self):
        '''List all tasks'''
        return DAO.getall()

    @ns.doc('create_todo',security='apikey')
    @token_required
    @ns.expect(todo)
    @ns.marshal_with(todo, code=201)
    def post(self):
        '''Create a new task'''
        return DAO.create(api.payload), 201


@ns.route('/<int:id>')
@ns.response(404, 'Todo not found')
@ns.param('id', 'The task identifier')
class Todo(Resource):
    '''Show a single todo item and lets you delete them'''
    @ns.doc('get_todo')
    @ns.marshal_with(todo)
    def get(self, id):
        '''Fetch a given resource'''
        return DAO.get(id)

    @ns.doc('delete_todo',security='apikey')
    @token_required
    @ns.response(204, 'Todo deleted')
    def delete(self, id):
        '''Delete a task given its identifier'''
        DAO.delete(id)
        return '', 204

    @ns.doc(security='apikey')
    @token_required
    @ns.expect(todo)
    @ns.marshal_with(todo)
    def put(self, id):
        '''Update a task given its identifier'''
        return DAO.update(id, api.payload)

@ns.route('/start/<int:id>')
@ns.response(404, 'Todo not found')
@ns.param('id', 'The task identifier')
class TodoStart(Resource):
    @ns.doc('start_todo',security='apikey')
    @token_required
    @ns.response(201, 'Todo Started')
    def get(self, id):
        '''Start a task given its identifier'''
        return DAO.updatestatus(id,'In Progress'), 201
    
@ns.route('/finish/<int:id>')
@ns.response(404, 'Todo not found')
@ns.param('id', 'The task identifier')
class TodoFinish(Resource):
    @ns.doc('finish_todo',security='apikey')
    @token_required
    @ns.response(201, 'Todo Completed')
    def get(self, id):
        '''Finish a task given its identifier'''
        return DAO.updatestatus(id,'Finished'), 201

@ns.route('/overdue')
@ns.response(404, 'No Overdue Tasks')
class TodoOverdue(Resource):
    @ns.doc('overdues')
    @ns.response(201, 'Overdue Todos Displayed')
    def get(self):
        '''Overdue tasks displayed'''
        return DAO.getoverdue(), 201

@ns.route('/finished')
@ns.response(404, 'No Finished Tasks')
class TodoOverdue(Resource):
    @ns.doc('finished')
    @ns.response(201, 'Finished Todos Displayed')
    def get(self):
        '''Finished tasks displayed'''
        return DAO.getfinished(), 201

@ns.route('/due')
@ns.response(404, 'No Todo due on this date found')
@ns.param('due_date', 'The task due date specified')
class TodoDue(Resource):
    @ns.doc('due')
    @ns.response(201, 'Todos due on the date is Displayed')
    def get(self):
        '''Finish a task given its identifier'''
        date=request.args['due_date']
        return DAO.getdue(date), 201


if __name__ == '__main__':
    app.run(debug=True)