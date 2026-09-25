import math
import streamlit as st
from dataclasses import dataclass

st.set_page_config(page_title="Prediction Market Demo", page_icon="🏁", layout="wide")

B = 1000.0
FEE = 0.01

def lse(a,b):
    m=max(a,b)
    return m+math.log(math.exp(a-m)+math.exp(b-m))

def cost(qy, qn, b=B):
    return b*lse(qy/b, qn/b)

def prices(qy, qn, b=B):
    d=(qy-qn)/b
    if d>=0:
        e=math.exp(-min(d,700)); py=1/(1+e)
    else:
        e=math.exp(max(d,-700)); py=e/(1+e)
    return py,1-py

def shares_for_budget(side,gross,qy,qn,b=B):
    net=gross*(1-FEE)
    c0=cost(qy,qn,b)
    lo,hi=0.0,max(1.0,net*4)
    def tc(x):
        return (cost(qy+x,qn,b) if side=="YES" else cost(qy,qn+x,b))-c0
    while tc(hi)<net: hi*=2
    for _ in range(90):
        mid=(lo+hi)/2
        if tc(mid)<=net: lo=mid
        else: hi=mid
    return lo,net,gross-net

if "qy" not in st.session_state:
    st.session_state.update(qy=0.0, qn=0.0, cash=10000.0, yes=0.0, no=0.0,
                            volume=0.0, fees=0.0, lp=1000.0, cashin=0.0,
                            history=[0.5], result=None, votes=[])

st.title("🏁 Prediction Market — Demo LMSR")
st.caption("Prototipo dimostrativo locale • denaro virtuale • nessuna blockchain reale")

py,pn=prices(st.session_state.qy,st.session_state.qn)

c1,c2,c3,c4=st.columns(4)
c1.metric("YES — Ferrari", f"${py:.4f}", f"{py*100:.2f}%")
c2.metric("NO — Ferrari", f"${pn:.4f}", f"{pn*100:.2f}%")
c3.metric("Volume", f"${st.session_state.volume:,.2f}")
c4.metric("Saldo virtuale", f"${st.session_state.cash:,.2f}")

st.subheader("🏎️ La Ferrari vincerà il prossimo Gran Premio?")
st.line_chart({"YES": st.session_state.history}, height=220)

tab1,tab2,tab3=st.tabs(["💹 Trading","👤 Le mie posizioni","🛡️ Admin / Oracle"])

with tab1:
    left,right=st.columns([1.2,1])
    with left:
        side=st.radio("Posizione",["YES","NO"],horizontal=True)
        amount=st.number_input("Importo da investire ($)",min_value=1.0,value=100.0,step=50.0)
        sh,net,fee=shares_for_budget(side,amount,st.session_state.qy,st.session_state.qn)
        nq_y=st.session_state.qy+(sh if side=="YES" else 0)
        nq_n=st.session_state.qn+(sh if side=="NO" else 0)
        npy,npn=prices(nq_y,nq_n)
        current=py if side=="YES" else pn
        final=npy if side=="YES" else npn
        avg=net/sh if sh else 0
        st.info(f"""**Anteprima ordine**

Contratti stimati: **{sh:,.4f} {side}**  
Prezzo attuale: **${current:.4f}**  
Prezzo medio effettivo: **${avg:.4f}**  
Prezzo dopo l'ordine: **${final:.4f}**  
Fee: **${fee:.2f}**  
Slippage vs prezzo iniziale: **{(avg-current)*100:+.2f} cent**""")
        disabled=amount>st.session_state.cash or st.session_state.result is not None
        if st.button(f"Acquista {side}",type="primary",use_container_width=True,disabled=disabled):
            if side=="YES":
                st.session_state.qy+=sh; st.session_state.yes+=sh
            else:
                st.session_state.qn+=sh; st.session_state.no+=sh
            st.session_state.cash-=amount
            st.session_state.volume+=amount
            st.session_state.fees+=fee
            st.session_state.cashin+=net
            st.session_state.history.append(prices(st.session_state.qy,st.session_state.qn)[0])
            st.rerun()
    with right:
        st.markdown("#### Come leggere il mercato")
        st.write("YES e NO sommano sempre a $1. L'LMSR modifica il prezzo mentre l'ordine viene eseguito: ordini grandi generano più slippage.")
        st.markdown("#### Parametri")
        st.write(f"Liquidità LMSR **b = {B:,.0f}**")
        st.write(f"Fee trading **{FEE:.0%}**")
        st.write("Chiusura: **demo manuale**")
        st.write("Resolution: **consenso Oracle 3/5**")

with tab2:
    a,b,c=st.columns(3)
    a.metric("Contratti YES",f"{st.session_state.yes:,.4f}")
    b.metric("Contratti NO",f"{st.session_state.no:,.4f}")
    payout_yes=st.session_state.yes
    payout_no=st.session_state.no
    c.metric("Saldo cash",f"${st.session_state.cash:,.2f}")
    st.write(f"Se vince **YES**: payout posizione = **${payout_yes:,.2f}**")
    st.write(f"Se vince **NO**: payout posizione = **${payout_no:,.2f}**")

with tab3:
    assets=st.session_state.lp+st.session_state.cashin
    ly,ln=st.session_state.qy,st.session_state.qn
    worst=max(ly,ln)
    margin=assets-worst
    x1,x2,x3,x4=st.columns(4)
    x1.metric("Collateral LP",f"${st.session_state.lp:,.2f}")
    x2.metric("Asset garanzia",f"${assets:,.2f}")
    x3.metric("Passività max",f"${worst:,.2f}")
    x4.metric("Margine",f"${margin:,.2f}")
    st.progress(min(max(assets/(worst if worst else assets),0),1) if assets else 0)
    st.write("Stato solvibilità:", "✅ **SOLVIBILE**" if margin>=-1e-8 else "❌ **INSOLVENTE**")
    st.divider()
    st.markdown("#### Refertazione Oracle")
    cols=st.columns(5)
    votes=[]
    for i,col in enumerate(cols,1):
        with col:
            votes.append(st.selectbox(f"Oracle {i}",["—","YES","NO","INVALID"],key=f"oracle{i}"))
    if st.button("Calcola consenso Oracle",use_container_width=True):
        valid=[v for v in votes if v!="—"]
        counts={k:valid.count(k) for k in ["YES","NO","INVALID"]}
        winner=max(counts,key=counts.get)
        if counts[winner]>=3:
            st.session_state.result=winner
            st.success(f"Consenso {counts[winner]}/5 → {winner}")
        else:
            st.warning("Nessun consenso 3/5.")
    if st.session_state.result:
        st.success(f"Risultato provvisorio: {st.session_state.result}")
        if st.button("Esegui settlement",type="primary"):
            r=st.session_state.result
            if r=="YES": payout=st.session_state.yes
            elif r=="NO": payout=st.session_state.no
            else: payout=.5*(st.session_state.yes+st.session_state.no)
            st.session_state.cash+=payout
            st.session_state.yes=st.session_state.no=0.0
            st.toast(f"Settlement completato: ${payout:,.2f}")
            st.rerun()

st.divider()
if st.button("🔄 Reset demo"):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()
