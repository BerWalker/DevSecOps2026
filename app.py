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

# RF03: Criar campanha 
@app.route('/api/campaigns', methods=['GET', 'POST'])
def manage_campaigns():
    if request.method == 'POST':
        return jsonify({
            "status": "success",
            "message": "Campanha criada com sucesso.",
            "data": {"id": 101, "nome": "Campanha Natal", "status": "Rascunho"}
        }), 201
        
    return jsonify({
        "status": "success",
        "data": [
            {"id": 101, "nome": "Campanha Natal", "status": "Ativa"}
        ]
    }), 200

# RF04: Gestão de alvos 
@app.route('/api/campaigns/<int:campaign_id>/targets', methods=['GET', 'POST'])
def manage_targets(campaign_id):
    if request.method == 'POST':
        return jsonify({
            "status": "success",
            "message": "Alvo adicionado à campanha com sucesso.",
            "data": {"id": 50, "nome": "João Silva", "email": "joao@empresa.com"}
        }), 201
        
    return jsonify({
        "status": "success",
        "data": [
            {"id": 50, "nome": "João Silva", "email": "joao@empresa.com"}
        ]
    }), 200

@app.route('/api/campaigns/<int:campaign_id>/targets/import', methods=['POST'])
def import_targets(campaign_id):
    return jsonify({
        "status": "success",
        "message": "150 alvos importados com sucesso para a campanha."
    }), 201

# RF05: Gerar links de rastreamento 
@app.route('/api/campaigns/<int:campaign_id>/links/generate', methods=['POST'])
def generate_links(campaign_id):
    return jsonify({
        "status": "success",
        "message": "Links de rastreamento gerados para todos os alvos da campanha."
    }), 200

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

# RF07: Rastrear interações 
@app.route('/track/<string:token>', methods=['GET'])
def track_click(token):
    # Como é um acesso do alvo (passivo) não retorna JSON na prática (faria redirecionamento ou imagem de 1px)
    return jsonify({
        "status": "success",
        "message": "Interação registrada (IP, Geolocalização, Timestamp).",
        "token_rastreado": token
    }), 200

# RF08: Dashboard agregado 
@app.route('/api/analytics/dashboard', methods=['GET'])
def aggregate_dashboard():
    return jsonify({
        "status": "success",
        "data": {
            "total_campanhas": 12,
            "total_emails_enviados": 4500,
            "taxa_clique_geral": "15.4%",
            "vulnerabilidade_risco": "Médio"
        }
    }), 200

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