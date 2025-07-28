# bolao_app/routes.py
from flask import render_template, request, redirect, url_for, flash
from flask import current_app as app
from flask_login import login_user, logout_user, login_required, current_user
from .models import db, User, Partida, Time, Aposta, SolicitacaoApostaTardia
from .auth import admin_required
from datetime import datetime
from sqlalchemy import and_

@app.route('/')
@login_required
def index():
    print(f"DEBUG: Acessando rota / - current_user.is_authenticated: {current_user.is_authenticated}")
    # Buscar as próximas 5 partidas que ainda não começaram
    proximas_partidas = Partida.query.filter(
        Partida.data_partida > datetime.now()
    ).order_by(Partida.data_partida.asc()).limit(5).all()
    return render_template('index.html', proximas_partidas=proximas_partidas)

@app.route('/login', methods=['GET', 'POST'])
def login():
    print(f"DEBUG: Acessando rota /login - current_user.is_authenticated: {current_user.is_authenticated}")
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            print(f"DEBUG: Login bem-sucedido para {username}")
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Usuário ou senha inválidos.')
            print(f"DEBUG: Falha no login para {username}")
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    print(f"DEBUG: Acessando rota /logout - current_user.is_authenticated: {current_user.is_authenticated}")
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    print(f"DEBUG: Acessando rota /register - current_user.is_authenticated: {current_user.is_authenticated}")
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Este nome de usuário já existe.')
            return redirect(url_for('register'))
            
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Usuário criado com sucesso! Faça o login.')
        return redirect(url_for('login'))
        
    return render_template('register.html')

# --- Rotas de Admin ---

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    print(f"DEBUG: Acessando rota /admin/dashboard - current_user.is_authenticated: {current_user.is_authenticated}")
    return render_template('admin/dashboard.html')

@app.route('/admin/times', methods=['GET'])
@login_required
@admin_required
def gerenciar_times():
    print(f"DEBUG: Acessando rota /admin/times - current_user.is_authenticated: {current_user.is_authenticated}")
    times = Time.query.order_by(Time.nome.asc()).all()
    return render_template('admin/gerenciar_times.html', times=times)

@app.route('/admin/times/adicionar', methods=['POST'])
@login_required
@admin_required
def adicionar_time():
    print(f"DEBUG: Acessando rota /admin/times/adicionar - current_user.is_authenticated: {current_user.is_authenticated}")
    nome = request.form['nome']
    liga = request.form['liga']
    
    novo_time = Time(nome=nome, liga=liga)
    db.session.add(novo_time)
    db.session.commit()
    
    flash('Time adicionado com sucesso!')
    return redirect(url_for('gerenciar_times'))

@app.route('/admin/times/deletar/<int:time_id>', methods=['POST'])
@login_required
@admin_required
def deletar_time(time_id):
    print(f"DEBUG: Acessando rota /admin/times/deletar - current_user.is_authenticated: {current_user.is_authenticated}")
    time = Time.query.get_or_404(time_id)

    if Partida.query.filter(Partida.time1_id == time.id).first() or \
       Partida.query.filter(Partida.time2_id == time.id).first():
        flash('Não é possível deletar este time, pois há partidas associadas a ele.')
        return redirect(url_for('gerenciar_times'))

    db.session.delete(time)
    db.session.commit()
    flash('Time deletado com sucesso!')
    return redirect(url_for('gerenciar_times'))

@app.route('/admin/partidas')
@login_required
@admin_required
def gerenciar_partidas():
    print(f"DEBUG: Acessando rota /admin/partidas - current_user.is_authenticated: {current_user.is_authenticated}")
    partidas = Partida.query.order_by(Partida.data_partida.asc()).all()
    times = Time.query.order_by(Time.nome.asc()).all()
    return render_template('admin/gerenciar_partidas.html', partidas=partidas, times=times)

@app.route('/admin/partidas/adicionar', methods=['POST'])
@login_required
@admin_required
def adicionar_partida():
    print(f"DEBUG: Acessando rota /admin/partidas/adicionar - current_user.is_authenticated: {current_user.is_authenticated}")
    time1_id = request.form['time1_id']
    time2_id = request.form['time2_id']
    match_type = request.form['match_type']
    data_partida_str = request.form['data_partida']
    
    if time1_id == time2_id:
        flash('Os times de uma partida não podem ser iguais.')
        return redirect(url_for('gerenciar_partidas'))

    data_partida = datetime.strptime(data_partida_str, '%Y-%m-%dT%H:%M')
    
    nova_partida = Partida(time1_id=time1_id, time2_id=time2_id, match_type=match_type, data_partida=data_partida)
    db.session.add(nova_partida)
    db.session.commit()
    
    flash('Partida adicionada com sucesso!')
    return redirect(url_for('gerenciar_partidas'))

def calculate_bet_result(aposta):
    status = "Aguardando Resultado"
    pontos = 0
    if aposta.partida.resultado: # Se a partida já tem resultado
        if aposta.partida.match_type == 'MD1':
            if aposta.palpite_vencedor == aposta.partida.resultado:
                status = "Acertou o Vencedor (MD1)"
                pontos = 2
            else:
                status = "Errou"
        else: # MD3 ou MD5
            # Extrair o nome do vencedor do palpite (ex: "TimeA 2-1" -> "TimeA")
            palpite_vencedor_nome = aposta.palpite_vencedor.split(' ')[0]
            
            # Extrair o placar do palpite (ex: "TimeA 2-1" -> "2-1")
            palpite_placar_str = aposta.palpite_vencedor.split(' ')[1] if len(aposta.palpite_vencedor.split(' ')) > 1 else None
            
            # Extrair o nome do vencedor do resultado da partida
            partida_vencedor_nome = aposta.partida.resultado.split(' ')[0] if aposta.partida.resultado else None
            
            # Extrair o placar do resultado da partida
            partida_placar_str = f"{aposta.partida.score_time1}-{aposta.partida.score_time2}" if aposta.partida.score_time1 is not None and aposta.partida.score_time2 is not None else None

            if palpite_vencedor_nome == partida_vencedor_nome:
                status = "Acertou o Vencedor"
                pontos = 1
                if palpite_placar_str == partida_placar_str:
                    status = "Acertou o Placar"
                    pontos += 4 # 1 (vencedor) + 4 (placar) = 5 pontos
            else:
                status = "Errou"
    return status, pontos

@app.route('/minhas_apostas')
@login_required
def minhas_apostas():
    print(f"DEBUG: Acessando rota /minhas_apostas - current_user.is_authenticated: {current_user.is_authenticated}")
    apostas_com_status = []
    for aposta in current_user.apostas:
        status, pontos = calculate_bet_result(aposta)
        apostas_com_status.append({
            'aposta': aposta,
            'status': status,
            'pontos_ganhos': pontos
        })
    return render_template('minhas_apostas.html', apostas=apostas_com_status)

@app.route('/apostar', methods=['GET', 'POST'])
@login_required
def apostar():
    print(f"DEBUG: Acessando rota /apostar - current_user.is_authenticated: {current_user.is_authenticated}")
    if request.method == 'POST':
        partida_id = request.form['partida_id']
        partida = Partida.query.get_or_404(partida_id)
        
        if partida.data_partida < datetime.now():
            flash('Não é possível apostar em partidas que já começaram.')
            return redirect(url_for('apostar'))

        aposta_existente = Aposta.query.filter(and_(
            Aposta.user_id == current_user.id,
            Aposta.partida_id == partida_id
        )).first()

        if aposta_existente:
            flash('Você já apostou nesta partida!')
            return redirect(url_for('apostar'))

        if partida.match_type == 'MD1':
            palpite_vencedor = request.form['palpite_vencedor']
            if palpite_vencedor not in [partida.time1.nome, partida.time2.nome]:
                flash('Palpite inválido para MD1.')
                return redirect(url_for('apostar'))
        else: # MD3 ou MD5
            score1_str = request.form.get('score_time1')
            score2_str = request.form.get('score_time2')

            try:
                score1 = int(score1_str)
                score2 = int(score2_str)
            except (ValueError, TypeError):
                flash('Placar inválido. Ambos os placares devem ser números.')
                return redirect(url_for('apostar'))

            if score1 < 0 or score2 < 0:
                flash('Placar inválido. Ambos os placares devem ser não negativos.')
                return redirect(url_for('apostar'))

            if partida.match_type == 'MD3':
                if not ((score1 == 2 and score2 < 2) or (score2 == 2 and score1 < 2)):
                    flash('Placar inválido para MD3. Deve ser 2-0, 2-1, 0-2 ou 1-2.')
                    return redirect(url_for('apostar'))
            elif partida.match_type == 'MD5':
                if not ((score1 == 3 and score2 < 3) or (score2 == 3 and score1 < 3)):
                    flash('Placar inválido para MD5. Deve ser 3-0, 3-1, 3-2, 0-3, 1-3 ou 2-3.')
                    return redirect(url_for('apostar'))
            
            if score1 > score2:
                palpite_vencedor = f"{partida.time1.nome} {score1}-{score2}"
            elif score2 > score1:
                palpite_vencedor = f"{partida.time2.nome} {score2}-{score1}"
            else:
                flash('Placar inválido. Não pode haver empate.')
                return redirect(url_for('apostar'))

        nova_aposta = Aposta(user_id=current_user.id, partida_id=partida_id, palpite_vencedor=palpite_vencedor)
        db.session.add(nova_aposta)
        db.session.commit()
        flash('Aposta registrada com sucesso!')
        return redirect(url_for('apostar')) # Redireciona após POST para evitar reenvio do formulário

    else: # Lógica para o método GET: exibe as partidas disponíveis para aposta
        # Partidas futuras que o usuário ainda não apostou
        partidas_para_exibir = []
        todas_partidas = Partida.query.order_by(Partida.data_partida.asc()).all()
        
        for partida in todas_partidas:
            aposta_existente = Aposta.query.filter(and_(
                Aposta.user_id == current_user.id,
                Aposta.partida_id == partida.id
            )).first()
            
            partidas_para_exibir.append({
                'partida': partida,
                'ja_apostou': aposta_existente is not None,
                'partida_iniciada': partida.data_partida < datetime.now()
            })

        return render_template('apostar.html', partidas_para_exibir=partidas_para_exibir)

@app.route('/solicitar_aposta_tardia', methods=['POST'])
@login_required
def solicitar_aposta_tardia():
    print(f"DEBUG: Acessando rota /solicitar_aposta_tardia - current_user.is_authenticated: {current_user.is_authenticated}")
    partida_id = request.form['partida_id']
    partida = Partida.query.get_or_404(partida_id)

    # Validações básicas (similar à aposta normal, mas sem verificar data_partida)
    if partida.match_type == 'MD1':
        palpite_vencedor = request.form['palpite_vencedor']
        if palpite_vencedor not in [partida.time1.nome, partida.time2.nome]:
            flash('Palpite inválido para MD1.')
            return redirect(url_for('apostar'))
    else: # MD3 ou MD5
        score1_str = request.form.get('score_time1')
        score2_str = request.form.get('score_time2')

        try:
            score1 = int(score1_str)
            score2 = int(score2_str)
        except (ValueError, TypeError):
            flash('Placar inválido. Ambos os placares devem ser números.')
            return redirect(url_for('apostar'))

        if score1 < 0 or score2 < 0:
            flash('Placar inválido. Ambos os placares devem ser não negativos.')
            return redirect(url_for('apostar'))

        if partida.match_type == 'MD3':
            if not ((score1 == 2 and score2 < 2) or (score2 == 2 and score1 < 2)):
                flash('Placar inválido para MD3. Deve ser 2-0, 2-1, 0-2 ou 1-2.')
                return redirect(url_for('apostar'))
        elif partida.match_type == 'MD5':
            if not ((score1 == 3 and score2 < 3) or (score2 == 3 and score1 < 3)):
                flash('Placar inválido para MD5. Deve ser 3-0, 3-1, 3-2, 0-3, 1-3 ou 2-3.')
                return redirect(url_for('apostar'))
        
        if score1 > score2:
            palpite_vencedor = f"{partida.time1.nome} {score1}-{score2}"
        elif score2 > score1:
            palpite_vencedor = f"{partida.time2.nome} {score2}-{score1}"
        else:
            flash('Placar inválido. Não pode haver empate.')
            return redirect(url_for('apostar'))

    # Criar a solicitação de aposta tardia
    nova_solicitacao = SolicitacaoApostaTardia(
        user_id=current_user.id,
        partida_id=partida_id,
        palpite_vencedor=palpite_vencedor,
        status='pendente'
    )
    db.session.add(nova_solicitacao)
    db.session.commit()
    flash('Sua solicitação de aposta tardia foi enviada para aprovação!')
    return redirect(url_for('apostar'))

    # Lógica para o método GET: exibe as partidas disponíveis para aposta
    # Partidas futuras que o usuário ainda não apostou
    partidas_para_exibir = []
    todas_partidas = Partida.query.order_by(Partida.data_partida.asc()).all()
    
    for partida in todas_partidas:
        aposta_existente = Aposta.query.filter(and_(
            Aposta.user_id == current_user.id,
            Aposta.partida_id == partida.id
        )).first()
        
        partidas_para_exibir.append({
            'partida': partida,
            'ja_apostou': aposta_existente is not None,
            'partida_iniciada': partida.data_partida < datetime.now()
        })

    return render_template('apostar.html', partidas_para_exibir=partidas_para_exibir)

@app.route('/mudar_senha', methods=['GET', 'POST'])
@login_required
def mudar_senha():
    print(f"DEBUG: Acessando rota /mudar_senha - current_user.is_authenticated: {current_user.is_authenticated}")
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_new_password = request.form['confirm_new_password']

        if not current_user.check_password(current_password):
            flash('Senha atual incorreta.')
        elif new_password != confirm_new_password:
            flash('A nova senha e a confirmação não coincidem.')
        elif len(new_password) < 6: 
            flash('A nova senha deve ter pelo menos 6 caracteres.')
        else:
            current_user.set_password(new_password)
            db.session.commit()
            flash('Sua senha foi alterada com sucesso!')
            return redirect(url_for('index'))

    return render_template('mudar_senha.html')

@app.route('/ranking')
@login_required
def ranking():
    print(f"DEBUG: Acessando rota /ranking - current_user.is_authenticated: {current_user.is_authenticated}")
    users = User.query.all()
    ranking_data = []

    for user in users:
        pontos_totais = 0
        for aposta in user.apostas:
            status, pontos = calculate_bet_result(aposta)
            pontos_totais += pontos
        ranking_data.append({'username': user.username, 'pontos': pontos_totais})

    ranking_data.sort(key=lambda x: x['pontos'], reverse=True)

    return render_template('ranking.html', ranking=ranking_data)

@app.route('/admin/partidas/editar/<int:partida_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_partida(partida_id):
    print(f"DEBUG: Acessando rota /admin/partidas/editar - current_user.is_authenticated: {current_user.is_authenticated}")
    partida = Partida.query.get_or_404(partida_id)
    times = Time.query.order_by(Time.nome.asc()).all()

    if request.method == 'POST':
        partida.time1_id = request.form['time1_id']
        partida.time2_id = request.form['time2_id']
        partida.match_type = request.form['match_type']
        partida.data_partida = datetime.strptime(request.form['data_partida'], '%Y-%m-%dT%H:%M')
        
        if partida.match_type == 'MD1':
            partida.resultado = request.form['resultado'] if request.form['resultado'] else None
            partida.score_time1 = None
            partida.score_time2 = None
        else: 
            score_time1 = request.form.get('score_time1', type=int)
            score_time2 = request.form.get('score_time2', type=int)

            if score_time1 is None or score_time2 is None or score_time1 < 0 or score_time2 < 0:
                flash('Placar inválido. Ambos os placares devem ser números não negativos.')
                return redirect(url_for('editar_partida', partida_id=partida.id))

            if partida.match_type == 'MD3':
                if not ((score_time1 == 2 and score_time2 < 2) or (score_time2 == 2 and score_time1 < 2)):
                    flash('Placar inválido para MD3. Deve ser 2-0, 2-1, 0-2 ou 1-2.')
                    return redirect(url_for('editar_partida', partida_id=partida.id))
            elif partida.match_type == 'MD5':
                if not ((score_time1 == 3 and score_time2 < 3) or (score_time2 == 3 and score_time1 < 3)):
                    flash('Placar inválido para MD5. Deve ser 3-0, 3-1, 3-2, 0-3, 1-3 ou 2-3.')
                    return redirect(url_for('editar_partida', partida_id=partida.id))

            partida.score_time1 = score_time1
            partida.score_time2 = score_time2

            if score_time1 > score_time2:
                partida.resultado = partida.time1.nome
            elif score_time2 > score_time1:
                partida.resultado = partida.time2.nome
            else:
                partida.resultado = None 

        if partida.time1_id == partida.time2_id:
            flash('Os times de uma partida não podem ser iguais.')
            return redirect(url_for('editar_partida', partida_id=partida.id))

        db.session.commit()
        flash('Partida atualizada com sucesso!')
        return redirect(url_for('gerenciar_partidas'))

    return render_template('admin/editar_partida.html', partida=partida, times=times)

@app.route('/admin/partidas/deletar/<int:partida_id>', methods=['POST'])
@login_required
@admin_required
def deletar_partida(partida_id):
    print(f"DEBUG: Acessando rota /admin/partidas/deletar - current_user.is_authenticated: {current_user.is_authenticated}")
    partida = Partida.query.get_or_404(partida_id)
    
    Aposta.query.filter_by(partida_id=partida.id).delete()
    
    db.session.delete(partida)
    db.session.commit()
    flash('Partida e suas apostas relacionadas deletadas com sucesso!')
    return redirect(url_for('gerenciar_partidas'))

@app.route('/admin/usuarios')
@login_required
@admin_required
def gerenciar_usuarios():
    print(f"DEBUG: Acessando rota /admin/usuarios - current_user.is_authenticated: {current_user.is_authenticated}")
    users = User.query.order_by(User.username.asc()).all()
    return render_template('admin/gerenciar_usuarios.html', users=users)

@app.route('/admin/usuarios/editar/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_usuario(user_id):
    print(f"DEBUG: Acessando rota /admin/usuarios/editar - current_user.is_authenticated: {current_user.is_authenticated}")
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        new_username = request.form['username']
        is_admin = 'is_admin' in request.form

        existing_user = User.query.filter_by(username=new_username).first()
        if existing_user and existing_user.id != user.id:
            flash('Este nome de usuário já está em uso.')
            return redirect(url_for('editar_usuario', user_id=user.id))

        user.username = new_username
        user.is_admin = is_admin
        db.session.commit()
        flash('Usuário atualizado com sucesso!')
        return redirect(url_for('gerenciar_usuarios'))

    return render_template('admin/editar_usuario.html', user=user)

@app.route('/admin/usuarios/redefinir_senha/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def redefinir_senha_usuario(user_id):
    print(f"DEBUG: Acessando rota /admin/usuarios/redefinir_senha - current_user.is_authenticated: {current_user.is_authenticated}")
    user = User.query.get_or_404(user_id)

    import secrets
    import string
    alphabet = string.ascii_letters + string.digits
    temp_password = ''.join(secrets.choice(alphabet) for i in range(10)) 

    user.set_password(temp_password)
    db.session.commit()

    flash(f'A senha de {user.username} foi redefinida para: {temp_password}. Por favor, informe ao usuário e peça para ele alterar a senha após o primeiro login.')
    return redirect(url_for('editar_usuario', user_id=user.id))

@app.route('/admin/usuarios/deletar/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def deletar_usuario(user_id):
    print(f"DEBUG: Acessando rota /admin/usuarios/deletar - current_user.is_authenticated: {current_user.is_authenticated}")
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash('Você não pode deletar sua própria conta de administrador.')
        return redirect(url_for('gerenciar_usuarios'))

    Aposta.query.filter_by(user_id=user.id).delete()

    db.session.delete(user)
    db.session.commit()
    flash('Usuário e suas apostas relacionadas deletados com sucesso!')
    return redirect(url_for('gerenciar_usuarios'))

@app.route('/admin/apostas')
@login_required
@admin_required
def gerenciar_apostas():
    print(f"DEBUG: Acessando rota /admin/apostas - current_user.is_authenticated: {current_user.is_authenticated}")
    apostas = Aposta.query.order_by(Aposta.id.desc()).all()
    return render_template('admin/gerenciar_apostas.html', apostas=apostas)

@app.route('/admin/apostas/deletar/<int:aposta_id>', methods=['POST'])
@login_required
@admin_required
def deletar_aposta(aposta_id):
    print(f"DEBUG: Acessando rota /admin/apostas/deletar - current_user.is_authenticated: {current_user.is_authenticated}")
    aposta = Aposta.query.get_or_404(aposta_id)
    db.session.delete(aposta)
    db.session.commit()
    flash('Aposta deletada com sucesso!')
    return redirect(url_for('gerenciar_apostas'))

@app.route('/admin/solicitacoes_apostas')
@login_required
@admin_required
def gerenciar_solicitacoes_apostas():
    print(f"DEBUG: Acessando rota /admin/solicitacoes_apostas - current_user.is_authenticated: {current_user.is_authenticated}")
    solicitacoes = SolicitacaoApostaTardia.query.filter_by(status='pendente').order_by(SolicitacaoApostaTardia.timestamp.asc()).all()
    return render_template('admin/gerenciar_solicitacoes_apostas.html', solicitacoes=solicitacoes)

@app.route('/admin/solicitacoes_apostas/aprovar/<int:solicitacao_id>', methods=['POST'])
@login_required
@admin_required
def aprovar_solicitacao_aposta(solicitacao_id):
    print(f"DEBUG: Acessando rota /admin/solicitacoes_apostas/aprovar - current_user.is_authenticated: {current_user.is_authenticated}")
    solicitacao = SolicitacaoApostaTardia.query.get_or_404(solicitacao_id)
    
    if solicitacao.status == 'pendente':
        # Criar a aposta real
        nova_aposta = Aposta(
            user_id=solicitacao.user_id,
            partida_id=solicitacao.partida_id,
            palpite_vencedor=solicitacao.palpite_vencedor
        )
        db.session.add(nova_aposta)
        solicitacao.status = 'aprovada'
        db.session.commit()
        flash('Solicitação de aposta tardia aprovada e aposta criada!')
    else:
        flash('Esta solicitação já foi processada.')
    return redirect(url_for('gerenciar_solicitacoes_apostas'))

@app.route('/admin/solicitacoes_apostas/rejeitar/<int:solicitacao_id>', methods=['POST'])
@login_required
@admin_required
def rejeitar_solicitacao_aposta(solicitacao_id):
    print(f"DEBUG: Acessando rota /admin/solicitacoes_apostas/rejeitar - current_user.is_authenticated: {current_user.is_authenticated}")
    solicitacao = SolicitacaoApostaTardia.query.get_or_404(solicitacao_id)
    
    if solicitacao.status == 'pendente':
        solicitacao.status = 'rejeitada'
        db.session.commit()
        flash('Solicitação de aposta tardia rejeitada.')
    else:
        flash('Esta solicitação já foi processada.')
    return redirect(url_for('gerenciar_solicitacoes_apostas'))
