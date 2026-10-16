# Genera libretto-lotta/index.html unendo i dati delle tecniche (doppia gamba + seatbelt toss).
# Uso: python3 gen_libretto.py <cartella con vid/steps_meta.json, vid/sprite_meta.json della doppia> <cartella seatbelt con steps_meta.json, sprite_meta.json>
import json,sys,re,os
dv,sv=sys.argv[1],sys.argv[2]
src=open(os.path.join(os.path.dirname(__file__),'gen_html.py')).read().split('for s in S:')[0]
src=src.replace("'vid/steps_meta.json'",repr(dv+'/vid/steps_meta.json')).replace("'vid/sprite_meta.json'",repr(dv+'/vid/sprite_meta.json'))
ns={};exec(src,ns)
for s in ns['S']:s['pts']=ns['M'][s['n']]['pts']
doppia={'id':'doppia','nome':'Doppia gamba','titolo':'Doppia gamba, passo per passo','dir':'doppia','sp':ns['sp'],'steps':ns['S'],
 'lead':'Dieci fotogrammi reali del tiro alla doppia gamba, con ciò che si vede, ciò che dice l\'istruttore e il perché.',
 'leggi':'Il ragazzo in maglia verde, a destra, esegue la tecnica. L\'allenatore in nero, a sinistra, la subisce. I cerchi numerati indicano testa, mani, ginocchia e piedi del ragazzo che attacca. <b>Attenzione alla vista:</b> solo i passaggi 1-4 sono ripresi di lato; poi la camera si sposta e ogni foto dice da dove è ripresa.',
 'nota':'I passaggi 9 e 10 sono sfocati perché il movimento è veloce.'}
M={m['n']:m for m in json.load(open(sv+'/steps_meta.json'))}
sp=json.load(open(sv+'/sprite_meta.json'))
L='Laterale'
ST=[
{'n':1,'t':18.25,'titolo':'Guardia e inizio del tiro',
 'vede':'Kolat (maglia gialla, a destra) è in guardia bassa: ginocchia piegate, schiena inclinata in avanti, le mani davanti ai fianchi, aperte. Un piede è più avanti, vicino all\'avversario in nero, l\'altro è dietro. Lui è appena partito: non ha ancora toccato nessuno.',
 'dice':'«Faccio il mio tiro alla single leg.» Il video parte da quando la single leg è già stata fatta e l\'avversario difende.',
 'perche':'Il seatbelt toss non è un attacco da fermo: è un secondo tempo, che usi quando la single leg si blocca. Per questo il video parte dal tiro.'},
{'n':2,'t':19.5,'titolo':'Contatto: l\'avversario fa il whizzer',
 'vede':'I due si toccano. L\'avversario passa un braccio sopra la spalla di Kolat e lo preme verso il basso; Kolat tiene la testa sotto il suo petto e le mani cercano le sue gambe. I piedi dell\'avversario si stringono e la gamba è appena sollevata.',
 'dice':'«Lui fa il whizzer.» Il whizzer è il braccio che passa sopra la spalla dell\'attaccante e lo schiaccia verso il tappeto.',
 'perche':'È la difesa classica alla single leg: con il whizzer l\'avversario ti appesantisce la spalla e non ti lascia salire. Da qui in poi Kolat non può più rialzarsi dritto con facilità.'},
{'n':3,'t':21.0,'titolo':'Single leg con un ginocchio a terra',
 'vede':'Kolat è abbassato su un ginocchio appoggiato al tappeto e tiene la gamba dell\'avversario con entrambe le mani, vicino al ginocchio. La sua testa è premuta contro le costole dell\'avversario; il braccio dell\'avversario è sopra la sua schiena. Il piede dell\'avversario resta a terra tra le gambe di Kolat.',
 'dice':'«Cerca di tenere il piede dentro il mio cavallo. Non vuole che lo porti fuori, sull\'anca o dentro.»',
 'perche':'Finché il piede dell\'avversario resta tra le tue gambe, la gamba non esce: lui ha una base e tu non puoi sollevarla. Lo scopo della tecnica è risolvere questo stallo.'},
{'n':4,'t':24.0,'titolo':'Lo stallo: Kolat si alza, la gamba resta bloccata',
 'vede':'Kolat è di nuovo in piedi, piegato in avanti, con la testa contro il torace dell\'avversario. Le mani sono unite dietro la gamba catturata, che resta ripiegata sotto il suo braccio. L\'avversario sta su un piede solo, con la schiena inclinata in avanti, il braccio libero penzola verso il tappeto.',
 'dice':'«Siamo bloccati in questa posizione. Non riesco a far uscire il piede. Tutto ciò che voglio fare ora è salire.»',
 'perche':'Non spingere né tirare a vuoto: se il piede non esce, il piano è salire lungo il corpo dell\'avversario fino a un\'altra presa. È questa la decisione chiave della tecnica.'},
{'n':5,'t':28.0,'titolo':'Salire con la mano, in profondità',
 'vede':'La testa di Kolat resta premuta contro l\'avversario. La mano sale lungo la gamba catturata, dalla caviglia verso il ginocchio; l\'altra mano la accompagna. I piedi di Kolat restano fermi e larghi, le ginocchia piegate: sale con le mani, non alzandosi in piedi.',
 'dice':'«Prendo questa mano e salgo, vado in profondità dietro il ginocchio.»',
 'perche':'Più la mano è profonda dietro il ginocchio, più la gamba è controllata e meno spazio ha lui per ritrarla. Si sale con le mani perché la schiena non si deve sollevare e il whizzer non deve prendere spazio.'},
{'n':6,'t':30.5,'titolo':'Avvolgere dietro il ginocchio',
 'vede':'Il braccio di Kolat passa dietro il ginocchio dell\'avversario e si chiude: il ginocchio dell\'avversario è ora nell\'incavo del braccio. La testa è ancora sotto il suo petto e i piedi di Kolat sono rimasti dove erano.',
 'dice':'«Una volta che ho avvolto, adesso posso cambiare.»',
 'perche':'La gamba è controllata dal gomito, non solo dalla mano. Solo ora si può lasciare la presa di prima senza che l\'avversario la ritragga: il cambio si fa quando la gamba è già al sicuro.'},
{'n':7,'t':34.5,'titolo':'Il cambio verso il seatbelt',
 'vede':'Le mani di Kolat si uniscono e la gamba è tenuta con la mano e l\'avambraccio. Un braccio comincia a passare attorno al busto dell\'avversario, ancora sotto la sua ascella. Il corpo di Kolat non si è mosso: cambiano solo le braccia.',
 'dice':'«Posso cambiare e andare alla seatbelt.»',
 'perche':'Il cambio è la parte che richiede tempo, perché le braccia lasciano una presa per prenderne un\'altra. Si fa da fermi e a testa premuta, per non dargli il tempo di scappare.'},
{'n':8,'t':40.0,'titolo':'Seatbelt: braccio attorno al busto, profondo',
 'vede':'Il braccio di Kolat è passato attorno alla vita dell\'avversario e l\'altro braccio completa la presa, come una cintura di sicurezza. La testa di Kolat è contro le sue costole, il peso in avanti. L\'avversario ha ancora un piede a terra e una mano appoggiata al proprio ginocchio.',
 'dice':'«Così profondo: ho la seatbelt.»',
 'perche':'Una presa profonda attorno al busto serve a farlo caricare sulle tue anche quando ti giri. Se la presa è superficiale, nell\'arco si scivola via.'},
{'n':9,'t':40.75,'titolo':'Passo inverso: il piede attraversa il suo corpo',
 'vede':'Kolat sposta un piede con un passo largo, di taglio, davanti al corpo dell\'avversario, e inizia a girarsi: il busto passa da frontale a dorso verso la camera. Il piede che passa è quello dietro. Le braccia restano chiuse attorno al busto.',
 'dice':'«Faccio un passo inverso. Prendo questa gamba e voglio passare attraverso il suo corpo, per l\'arco all\'indietro.»',
 'perche':'Il passo porta le tue anche sotto le sue. Se il piede non attraversa abbastanza, hai la schiena davanti al suo petto, non sotto.'},
{'n':10,'t':41.25,'titolo':'Anche sotto di lui, ginocchia piegate',
 'vede':'Kolat è ora di schiena alla camera, accovacciato con le ginocchia aperte e i piedi larghi. L\'avversario è piegato sopra la sua schiena, con le gambe che stanno ormai lasciando il tappeto. Il busto di Kolat è completamente girato.',
 'dice':'«Ora faccio l\'arco.»',
 'perche':'Ti accovacci per metterti sotto di lui, poi lo sollevi spingendo le anche in avanti e verso l\'alto, non tirando con le braccia.'},
{'n':11,'t':41.55,'titolo':'L\'arco: lui passa sopra la schiena',
 'vede':'Un solo istante, sfocato: l\'avversario è sollevato sopra la schiena di Kolat, con le gambe in aria. Kolat ha i piedi ancora larghi e ben piantati.',
 'dice':'«Poi l\'arco.»',
 'perche':'La spinta vera si fa con le gambe e le anche, che si distendono in un movimento solo.'},
{'n':12,'t':42.0,'titolo':'Atterraggio: lui sulla schiena, Kolat sopra',
 'vede':'L\'avversario sta cadendo di schiena, con le gambe in aria, e Kolat è sopra di lui, con le braccia ancora attorno al busto. La caduta dura meno di mezzo secondo.',
 'dice':'La trascrizione si ferma qui: nel video seguono azioni dal vivo.',
 'perche':'Il punto più alto è il lancio, ma la tecnica finisce quando atterri sopra, in controllo. Un seatbelt toss ben fatto dà punti e posizione.'}]
for s in ST:s['pts']=M[s['n']]['pts'];s['vista']=L
sb={'id':'seatbelt','nome':'Seatbelt toss','titolo':'Seatbelt toss, passo per passo','dir':'seatbelt','sp':sp,'steps':ST,
 'lead':'Dodici fotogrammi reali del seatbelt toss di Cary Kolat: una single leg che si blocca contro un whizzer e si trasforma in un lancio con l\'arco.',
 'leggi':'Kolat, in maglia gialla a destra, esegue la tecnica. L\'avversario, in nero a sinistra, la subisce. La camera è sempre ferma e di lato, quindi tutti i passaggi sono ripresi dalla stessa vista. I cerchi numerati indicano testa, mani, piedi e ginocchio di Kolat.',
 'nota':'Nel video l\'istruttore dice che questa tecnica vale «3, a volte 5» punti, secondo l\'arco. Il lato (destro o sinistro) di piedi e braccia non è confermato dalla trascrizione: nelle descrizioni uso «un piede» e «il piede dietro» invece di inventare un lato.'}
tpl=open(os.path.join(os.path.dirname(__file__),'libretto_template.html')).read()
out=tpl.replace('/*DATA*/null',json.dumps({'techs':[doppia,sb]},ensure_ascii=False))
open(os.path.join(os.path.dirname(__file__),'..','index.html'),'w').write(out);print(len(out))
