# Parâmetros para construção da matriz de demanda (modelo gravitacional)

GAMMA = 0.01
T = 100000

# Parâmetros do modelo de custo de coleta
RHO_COL = 5      # ρ^col: pacotes coletados por parada
Q_COL = 150        # Q^col: capacidade do veículo de coleta, em pacotes 
BETA_COL = 1.15  # β^col: coeficiente de aproximação contínua
C_COL = 2.50       # c^col: custo operacional por km do veículo de coleta, em R$/km


# Parâmetros do modelo de custo de entrega
RHO_ENT = 5      # ρ^ENT: pacotes entregues por parada
Q_ENT = 150        # Q^ENT: capacidade do veículo de entrega, em pacotes 
BETA_ENT = 1.15 # β^ENT: coeficiente de aproximação contínua
C_ENT = 2.50       # c^ENT: custo operacional por km do veículo de entrega, em R$/km

#0,90 → malha euclidiana (rodovias relativamente diretas)
#1,15 → malha tipo grade/Manhattan
#0,712–0,80 → piso teórico assintótico (malha viária super otimizada)
