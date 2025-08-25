from flask import Flask, jsonify, request

app = Flask(__name__)

tasks = []
task_id_counter = 1

@app.route('/tasks', methods=['GET'])
def get_tasks():
    """Obtém a lista de todas as tarefas."""
    return jsonify(tasks)

@app.route('/tasks', methods=['POST'])
def create_task():
    """Cria uma nova tarefa."""
    global task_id_counter
    data = request.get_json()
    if not data or not 'title' in data:
        return jsonify({'error': 'O título é obrigatório'}), 400
    
    new_task = {
        'id': task_id_counter,
        'title': data['title'],
        'done': False
    }
    tasks.append(new_task)
    task_id_counter += 1
    return jsonify(new_task), 201

@app.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Atualiza uma tarefa existente."""
    task = next((task for task in tasks if task['id'] == task_id), None)
    if not task:
        return jsonify({'error': 'Tarefa não encontrada'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    task['title'] = data.get('title', task['title'])
    task['done'] = data.get('done', task['done'])
    return jsonify(task)

@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Apaga uma tarefa."""
    global tasks
    task = next((task for task in tasks if task['id'] == task_id), None)
    if not task:
        return jsonify({'error': 'Tarefa não encontrada'}), 404
    
    tasks = [t for t in tasks if t['id'] != task_id]
    return jsonify({'result': True})

if __name__ == '__main__':
    app.run(debug=True)
