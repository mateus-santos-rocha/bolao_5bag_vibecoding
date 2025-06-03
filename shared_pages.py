# Arquivo: shared_pages.py
# Descrição: Funções para páginas compartilhadas, como o ranking e a nova evolução.

import streamlit as st
import pandas as pd
from collections import defaultdict
from datetime import datetime

def show_ranking_page(championship_id, championship_name):
    # ... (código da show_ranking_page permanece o MESMO da última versão)
    st.subheader(f"Ranking Geral - Campeonato: {championship_name}")
    if championship_id is None:
        st.warning("Nenhum campeonato ativo. Contate o administrador."); return
    users = st.session_state.get("users", {}) 
    bets = st.session_state.get("bets", []) 
    matches = st.session_state.get("matches", []) 
    if not users: st.info("Nenhum jogador registrado."); return
    player_scores = defaultdict(int) 
    for uname, udata in users.items():
        if not udata.get("is_admin", False): player_scores[uname] = 0
    for bet_item in bets:
        match_item = next((m for m in matches if m.get('id') == bet_item.get('match_id')), None)
        user_item = users.get(bet_item.get('user_id'))
        if match_item and match_item.get('status')=="Finalizada" and user_item and not user_item.get("is_admin",False):
            player_scores[bet_item.get('user_id')] += bet_item.get('points_awarded', 0)
    
    # Filtra jogadores que não são admin para o ranking
    non_admin_players = {player: score for player, score in player_scores.items() if player in users and not users[player].get("is_admin")}

    if not non_admin_players: 
        st.info("Nenhum jogador (não admin) para exibir no ranking ou nenhum ponto computado.")
        return

    sorted_p = sorted(non_admin_players.items(), key=lambda item: (-item[1], item[0])) 
    rank_data = [{"Pos.": i+1, "Jogador": p, "Pontos": s} for i, (p, s) in enumerate(sorted_p)]
    if rank_data: st.dataframe(pd.DataFrame(rank_data), hide_index=True, use_container_width=True)
    else: st.info("Ranking indisponível para este campeonato.")


def get_historical_rankings(championship_id):
    """
    Calcula o histórico de pontuações e posições dos jogadores ao longo do campeonato.
    Retorna uma lista de dicionários: [{'date': ..., 'player': ..., 'position': ..., 'score': ...}]
    """
    historical_data = []
    if championship_id is None:
        return historical_data

    users = st.session_state.get("users", {})
    all_bets_for_champ = st.session_state.get("bets", [])
    all_matches_for_champ = st.session_state.get("matches", [])

    if not all_matches_for_champ or not users:
        return historical_data

    finalized_matches = [m for m in all_matches_for_champ if m.get('status') == "Finalizada" and m.get('datetime_iso')]
    if not finalized_matches:
        return historical_data

    # Ordena as partidas finalizadas pela data/hora do evento
    finalized_matches.sort(key=lambda m: m['datetime_iso'])

    # Obtém todas as datas únicas em que partidas foram finalizadas (consideradas como "eventos de pontuação")
    snapshot_dates = sorted(list(set(datetime.fromisoformat(m['datetime_iso']).date() for m in finalized_matches)))

    if not snapshot_dates:
        return historical_data
        
    # Inicializa a pontuação de todos os jogadores (não admin)
    player_usernames = [uname for uname, udata in users.items() if not udata.get("is_admin", False)]
    if not player_usernames:
        return historical_data # Não há jogadores para rastrear

    # Adiciona um ponto inicial "antes do campeonato começar" para todas as linhas começarem do mesmo lugar (opcional)
    # Para simplificar, vamos começar com a data da primeira partida finalizada.
    # Ou, para ter um "dia 0", podemos usar a data da primeira partida do campeonato, mesmo que não finalizada.
    # Por ora, a primeira data será a da primeira partida finalizada.

    for snap_date in snapshot_dates:
        current_scores_at_snapshot = defaultdict(int)
        for player_uname in player_usernames: # Garante que todos os jogadores estejam no snapshot
            current_scores_at_snapshot[player_uname] = 0

        # Calcula a pontuação acumulada até esta data de snapshot
        for match in finalized_matches:
            match_event_date = datetime.fromisoformat(match['datetime_iso']).date()
            if match_event_date <= snap_date: # Considera esta partida e todas as anteriores
                # Encontra apostas para esta partida
                bets_for_this_match = [b for b in all_bets_for_champ if b.get('match_id') == match.get('id')]
                for bet in bets_for_this_match:
                    player_id = bet.get('user_id')
                    # Garante que estamos apenas contabilizando jogadores e não o admin
                    if player_id in player_usernames:
                        current_scores_at_snapshot[player_id] += bet.get('points_awarded', 0)
        
        # Prepara para rankear: lista de (jogador, pontuação)
        scores_list_for_ranking = [{'player': pid, 'score': s} for pid, s in current_scores_at_snapshot.items()]
        
        # Ordena: primeiro por pontuação (descendente), depois por nome (ascendente para desempate)
        scores_list_for_ranking.sort(key=lambda x: (-x['score'], x['player']))
        
        # Atribui posições (ranking "1224" - standard competition ranking)
        # Jogadores com mesma pontuação recebem a mesma posição.
        # O próximo rank pula de acordo com o número de jogadores empatados.
        # Ex: P1=100 (1º), P2=100 (1º), P3=90 (3º)
        
        last_score = float('-inf') # Alterado para -inf para ranking ascendente de posição
        current_rank = 0
        tie_count = 1 # Quantos estão empatados na posição atual
        
        for i, entry in enumerate(scores_list_for_ranking):
            if entry['score'] < last_score: # Se a pontuação é menor, novo rank
                current_rank += tie_count
                tie_count = 1
            elif i > 0 : # Mesmo score do anterior (empate), mas não é o primeiro da lista
                tie_count +=1
            
            # Se é o primeiro jogador ou a pontuação é diferente do primeiro,
            # current_rank é i+1. Se empatado, mantém o rank anterior.
            # Vamos usar o método de rank denso (1, 2, 2, 3) para visualização mais simples no gráfico
            # Para isso, precisamos de uma lógica diferente.

        # Lógica para rank denso (1, 2, 2, 3)
        unique_sorted_scores = sorted(list(set(s['score'] for s in scores_list_for_ranking)), reverse=True)
        score_to_rank_map = {score_val: rank_val + 1 for rank_val, score_val in enumerate(unique_sorted_scores)}

        for entry in scores_list_for_ranking:
            player_name = entry['player']
            player_score = entry['score']
            player_position = score_to_rank_map.get(player_score, len(player_usernames)) # Default para última pos se score não mapeado

            historical_data.append({
                "date": snap_date, # pd.to_datetime(snap_date) pode ser útil para o gráfico
                "player": player_name,
                "position": player_position,
                "score": player_score 
            })
            last_score = entry['score'] # Atualiza para o próximo loop (se fosse o ranking "1224")

    return historical_data


def show_evolution_page(championship_id, championship_name):
    """Exibe o gráfico de evolução da posição dos jogadores."""
    st.subheader(f"Evolução no Campeonato: {championship_name}")

    if championship_id is None:
        st.warning("Nenhum campeonato ativo selecionado. Por favor, contate o administrador.")
        return

    evolution_data = get_historical_rankings(championship_id)

    if not evolution_data:
        st.info("Ainda não há dados suficientes para mostrar a evolução (nenhuma partida finalizada com apostas ou nenhum jogador).")
        return

    df_evolution = pd.DataFrame(evolution_data)
    
    # Converte a coluna 'date' para datetime se ainda não for, para melhor formatação no eixo X
    df_evolution['date'] = pd.to_datetime(df_evolution['date'])

    if df_evolution.empty:
        st.info("Não foi possível gerar dados para o gráfico de evolução.")
        return

    # Streamlit espera que a coluna y seja numérica. Posição já é.
    # O gráfico de linha mostrará posições menores (1º, 2º) como "melhores" (mais acima se o eixo Y for invertido)
    # Por padrão, valores menores no eixo Y ficam mais abaixo. Isso é intuitivo para "posição".
    
    st.markdown("#### Posição dos Jogadores ao Longo do Tempo")
    st.caption("O eixo Y representa a posição no ranking (quanto menor, melhor).")

    # Verifica se há dados suficientes para plotar
    if len(df_evolution['date'].unique()) < 2 and len(df_evolution['player'].unique()) <=1 :
         st.info("É necessário pelo menos dois pontos no tempo ou mais de um jogador com dados para plotar a evolução.")
    elif df_evolution.empty:
        st.info("Sem dados para plotar.")
    else:
        # Pivotar a tabela para o formato que st.line_chart espera se não usar x,y,color
        # Formato longo: date, player, position
        # st.line_chart pode usar o formato longo diretamente com os parâmetros x, y, color
        
        # Para garantir que o eixo Y (posição) seja exibido corretamente (1 no topo, etc.)
        # podemos plotar -posição e ajustar os ticks, ou usar uma biblioteca mais flexível.
        # Por simplicidade, vamos plotar a posição diretamente. Menor é melhor.
        
        # Ajuste para garantir que todas as linhas tenham pontos em todas as datas para st.line_chart
        # Isso pode ser feito pivotando e depois despivotando, ou usando unstack/stack.
        try:
            df_pivot = df_evolution.pivot_table(index='date', columns='player', values='position')
            # Refillna para garantir que cada jogador tenha um valor em cada data (pode ser ffill ou bfill)
            df_pivot = df_pivot.ffill().bfill() 
            
            # st.line_chart(df_pivot) # Plota todas as colunas (jogadores) contra o índice (data)
            # Ou, usando o formato longo original, que é mais flexível para cores.
            # No entanto, st.line_chart com color pode não conectar pontos se houver NaNs.
            # O pivotamento acima com ffill/bfill ajuda a ter uma linha contínua.
            
            # A melhor forma para st.line_chart com múltiplas linhas é ter um DataFrame "largo":
            # Index: Date, Colunas: Player1_Position, Player2_Position, ...
            # Ou usar os argumentos x, y, color (mas cuidado com NaNs)

            # Usando formato longo com x, y, color. Pode precisar de ffill/bfill se houver dados faltando.
            # Para isso, precisamos garantir que cada jogador tenha uma entrada para cada data.
            # A forma mais robusta é criar um DataFrame completo com todas as combinações de data/jogador.
            all_dates = df_evolution['date'].unique()
            all_players = df_evolution['player'].unique()
            idx = pd.MultiIndex.from_product([all_dates, all_players], names=['date', 'player'])
            df_full_evolution = df_evolution.set_index(['date', 'player']).reindex(idx).reset_index()
            
            # Preencher NaNs na posição. Poderia ser com a última posição conhecida (ffill)
            # ou com uma posição "padrão" se o jogador não existia/não pontuou ainda.
            # Para o gráfico, ffill é razoável.
            df_full_evolution['position'] = df_full_evolution.groupby('player')['position'].ffill().bfill()
            
            if not df_full_evolution.empty and not df_full_evolution['position'].isnull().all():
                st.line_chart(df_full_evolution, x='date', y='position', color='player')
            else:
                st.info("Não há dados suficientes de posição após o preenchimento para plotar o gráfico.")

        except Exception as e:
            st.error(f"Erro ao gerar o gráfico de evolução: {e}")
            st.dataframe(df_evolution) # Mostra os dados brutos em caso de erro no pivot/plot

# --- FIM DO ARQUIVO: shared_pages.py ---