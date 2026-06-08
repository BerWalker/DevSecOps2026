from flask import Flask, jsonify, request

app = Flask(__name__)

# ==========================================
# SERVIÇO DE AUTENTICAÇÃO E USUÁRIOS
# ==========================================
# RF01 (login/logout/register): services/auth microservice (port 5001)

# RF02: Cadastro de operadores 
@app.route('/api/operators', methods=['GET', 'POST'])
def manage_operators():
    if request.method == 'POST':
        return jsonify({
            "status": "success",
            "message": "Operador criado com sucesso.",
            "data": {"id": 1, "nome": "Novo Operador", "email": "operador@brazucaphish.com"}
        }), 201
        
    return jsonify({
        "status": "success",
        "data": [
            {"id": 1, "nome": "Operador 1", "email": "op1@brazucaphish.com"}
        ]
    }), 200

@app.route('/api/operators/<int:operator_id>', methods=['PUT', 'DELETE'])
def update_delete_operator(operator_id):
    action = "atualizado" if request.method == 'PUT' else "removido"
    return jsonify({
        "status": "success",
        "message": f"Operador {operator_id} {action} com sucesso."
    }), 200


# ==========================================
# SERVIÇO DE CAMPANHAS (E ALVOS)
# ==========================================

# RF06: Enviar e-mails simulados 
@app.route('/api/campaigns/<int:campaign_id>/send', methods=['POST'])
def send_emails(campaign_id):
    return jsonify({
        "status": "success",
        "message": f"Disparo da campanha {campaign_id} iniciado com sucesso.",
        "data": {"alvos_notificados": 150}
    }), 200


# ==========================================
# SERVIÇO DE ANALYTICS E TRACKING
# ==========================================

# RF09: Dashboard por campanha 
@app.route('/api/analytics/campaigns/<int:campaign_id>', methods=['GET'])
def campaign_dashboard(campaign_id):
    return jsonify({
        "status": "success",
        "data": {
            "campanha_id": campaign_id,
            "emails_enviados": 150,
            "cliques_registrados": 32,
            "taxa_conversao": "21.3%",
            "detalhes_alvos": [
                {"email": "joao@empresa.com", "clicou": True, "ip": "192.168.1.100"}
            ]
        }
    }), 200

# RF10: Exportar relatório CSV 
@app.route('/api/analytics/campaigns/<int:campaign_id>/export', methods=['GET'])
def export_csv(campaign_id):
    # Para teste via JSON, retornando um payload confirmando a ação (poderia retornar text/csv na real)
    return jsonify({
        "status": "success",
        "message": f"Download do relatório CSV gerado para a campanha {campaign_id}.",
        "download_url": f"/static/reports/campanha_{campaign_id}_resultado.csv"
    }), 200

if __name__ == '__main__':
    # Inicializando o API Gateway local na porta 5000
    app.run(debug=True, host='0.0.0.0', port=5000)