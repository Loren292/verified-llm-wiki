# Verified LLM Wiki

*English: [README.md](README.md)*

Una extensión del patrón [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
de Andrej Karpathy. Leé primero su archivo de idea: este se apoya en él. Como el original, es un
archivo de idea. Se lo pegás a tu agente y arman juntos tu versión. El repo trae además una
plantilla, un verificador de solo lectura (`tools/wikicheck.py`) y un ejemplo chico resuelto.

## La versión corta

El patrón de Karpathy: en vez de buscar en los documentos crudos en cada pregunta, un LLM arma y
mantiene una wiki de archivos markdown que queda entre vos y tus fuentes. Un archivo de schema
(`CLAUDE.md`, `AGENTS.md`) le dice cómo. Ingiere fuentes, contesta preguntas, archiva las buenas
respuestas y cada tanto revisa la wiki (lint). El conocimiento se acumula en vez de reconstruirse
cada vez.

Este documento agrega una sola cosa: **una capa de verificación que no depende del modelo.**

En el original, el mismo LLM que escribe la wiki es el que la controla. Eso funciona mientras la
wiki es chica y hay poco en juego. Deja de funcionar cuando:

- la wiki respalda números que alguien tiene que defender;
- las fuentes cambian por debajo;
- varios agentes y personas escriben en ella al mismo tiempo.

Entonces la wiki parece coherente mientras está equivocada sin que nadie lo note.

Todo lo que sigue salió de un proyecto real que pasó por las tres cosas. Era un modelo de datos y
su documentación, mantenidos durante semanas por varios agentes de IA (Claude, Codex) y dos
personas en una misma carpeta compartida. Cada regla existe porque pasó un error concreto. Acá
están escritas en forma genérica.

## Qué sale mal sin esto

- **Los números copiados quedan viejos.** Una cifra se copia a una página de resumen, después la
  página de origen la corrige, y la copia queda. En una revisión, de 12 celdas viejas o mal de una página
  de resumen, 9 eran números o conteos copiados de otro lado.
- **"Decidido" se lee como "hecho".** Una página dice que un cambio se aplicó cuando solo se había
  acordado. Todo lo que viene después supone algo que no es cierto.
- **Las citas parecen correctas pero no lo son.** Un agente revisor devuelve hallazgos con citas.
  Las citas son reales, pero algunas apuntan a líneas equivocadas y algunos pasajes relevantes se
  saltearon sin aviso. En una prueba, la cobertura de un agente de extracción varió entre
  corridas: completa dos veces, 82 % otra. Todas las citas que devolvió eran perfectas, y solo un
  control mecánico completo notó lo que faltaba.
- **La autorrevisión no ve lo que el autor "ya sabe".** El agente que escribió una página lee lo
  que quiso decir, no lo que escribió.
- **Dos que escriben, un archivo.** Dos chats, o un chat y una persona con el archivo abierto, se
  pisan al guardar.
- **Las reglas se gastan.** Una regla escrita sin su porqué empieza a parecer una preferencia de
  estilo y se deja de cumplir.

## Principios

1. **Lo mecánico lo hace un script, el criterio lo pone el modelo.** Buscar, contar, cruzar listas
   y comparar valores entre archivos le toca a un script: lo hace igual cada vez, con cobertura
   completa. El modelo decide, diseña, redacta y juzga si algo es de verdad una contradicción. Un
   modelo barato al que se le pide criterio se equivoca. Si no se le pide criterio, hace lo mismo
   que grep, más lento y con cobertura variable.
2. **Orden de verdad: dato real > wiki > lo que cualquiera le cuente al agente**, vos incluido. El
   dato real es lo que se puede medir: los datos, el código, el sistema en sí.
   - Si la wiki contradice al dato real, gana el dato real y se registra un hallazgo.
   - Si lo que le contás al agente contradice a la wiki, gana la wiki y el agente te lo dice. Tus
     resúmenes a veces van a estar mal, y para eso está la wiki.
3. **Medí antes de afirmar.** Si algo se puede medir, se mide antes de escribirlo. "No alcanza
   para afirmarlo" es mejor que una conclusión prolija sin respaldo.
4. **Los controles tienen que fallar fuerte.** Un control cuyo valor esperado se mueve con el reloj
   (la fecha de hoy, la última fila) siempre da bien y no controla nada.

## Arquitectura

Las tres capas de Karpathy se mantienen y se agrega una cuarta.

- **El dato real** (sus fuentes crudas). No siempre es inmutable: puede ser una base de datos, un
  código o un modelo que cambia todo el tiempo. La wiki registra *contra qué versión* se verificó
  cada afirmación.
- **La wiki,** separada en *estado* (qué es cierto ahora, qué está abierto) y *páginas* (temas,
  entidades, conceptos). Cada dato vive en un solo lugar. **Muchos archivos chicos:** ningún
  archivo de estado crece sin límite (ver 4 y 11).
- **El schema: solo método, nunca estado.** Ni números, ni decisiones, ni fechas, porque eso
  caduca. Un schema que solo tiene método no vence.
- **La capa de verificación** (nueva): un verificador de solo lectura, fotos del dato real, un
  registro de firmas y archivos de rol para la revisión independiente.

## Lo que se agrega

### 1. El lint lo hace un script, no el modelo

El lint de Karpathy le pide al LLM que busque contradicciones, afirmaciones viejas, páginas
huérfanas y links faltantes. Acá, todo lo que se puede controlar mecánicamente lo controla un
script de solo lectura, siempre, con cobertura completa. El script da **candidatos, no
veredictos**: el agente lee cada uno antes de reportarlo.

`wikicheck lint` corre siete controles:

| Control | Qué detecta |
|---|---|
| L1 Índice | Archivos que nadie anotó, entradas que apuntan a archivos borrados, entradas sin tipo, en el índice raíz y en el de cada área |
| L2 Links | `[[página]]` y `[[página#título]]` que no apuntan a nada |
| L3 Registro | IDs usados y nunca registrados, duplicados, "ejecutado" sin evidencia, decisiones anuladas que se siguen usando, ítems abiertos en el archivo, áreas que no existen |
| L4 Valores reemplazados | Un valor viejo que una corrección ya reemplazó y sigue en alguna página |
| L5 Procedencia | Páginas que salieron de una fuente que cambió después de escribirlas |
| L6 Log | Firmas fuera de orden, en el futuro (estimadas, no leídas del reloj), en el archivo de otro mes, o que no dicen qué se controló |
| L7 Reglas | Reglas del schema sin el error que las originó |

### 2. Decidido ≠ ejecutado

Cada decisión tiene dos estados separados, decidida y ejecutada. "Ejecutada" pide evidencia del
dato real (una diferencia, un valor medido, una foto), no de la wiki misma. Confundir los dos fue
el error más repetido del proyecto de donde sale esto.

La numeración separa las cosas:

| | Qué es |
|---|---|
| **D** | Decisión: dos caminos defendibles, uno elegido, con su porqué |
| **H** | Hallazgo: los datos mostraron algo que no se sabía |
| **T** | Pregunta a un tercero: la respuesta no está en los datos, así que va con lo que está en juego, medido |
| **P** | Decisión tuya pendiente, con lo que bloquea |

### 3. Un dato real que cambia: fotos y procedencia

Si el dato real cambia, "la wiki dice X" solo significa algo junto con "verificado contra la
versión V".

- Después de cada cambio verificado se saca una **foto**: el hash de cada archivo del dato real.
  La sesión siguiente arranca comparando contra la última foto, así sabe qué cambió en vez de
  creer lo que le cuentan.
- Una página que sale de una fuente anota el **hash** de esa fuente en su frontmatter. Si la
  fuente cambia, el lint marca la página como posiblemente vieja.

### 4. Archivos chicos: el registro es una tabla y cada entrada es una página

El proyecto detrás de esto guardaba las decisiones en un registro de cambios que crecía sin
parar. Llegó a unos 700 KB y hacían falta scripts solo para moverse en él. Así que, al estilo
Karpathy:

- `registry.md` tiene **solo tablas**: una fila por cada D, H, T y P, con estado, evidencia y un
  link a su página.
- **Cada ID tiene su página chica** (`registry/D12.md`) con el qué, el porqué, cómo se hizo,
  dónde más se calcula lo mismo y los controles. El estado no se repite en la página: vive solo
  en la tabla.
- **La cronología vive en `log.md`.** Como el log de Karpathy, se lee por la cola, nunca entero.

El agente lee una tabla corta y abre solo las páginas que toca el trabajo.

### 5. Apuntar, no copiar

Un número vive en un solo lugar y las otras páginas apuntan a él.

- Cuando se corrige un valor, el viejo va a una tabla de **valores reemplazados** (viejo, nuevo,
  desde cuándo, por qué), y el lint lo busca en todas las páginas. Para mencionar un valor viejo a
  propósito, como historia, se marca la línea con `(old)`.
- Un cambio que altera un cálculo dice **dónde más se calcula lo mismo**. Una vez se aplicó una
  corrección en una vista mientras otra vista calculaba la misma métrica por su lado con la regla
  vieja. Lo encontró alguien de afuera del proyecto.

### 6. Citas que un programa puede verificar

En Karpathy, la consulta contesta "con citas", pero nadie las controla. Acá, todo informe que cita
la wiki (los hallazgos de un revisor, una extracción) usa un formato fijo:

```
<<<CITE wiki/metrics.md 12-14
el texto exacto, copiado; "…" puede cortar, nunca reescribir
CITE>>>
```

El informe también declara qué leyó entero (`READ wiki/metrics.md 1-120`). `wikicheck cite`
controla todas las citas, no una muestra: si están en esas líneas, corridas o no aparecen. También
avisa qué archivos no se leyeron enteros y, dados los términos de búsqueda, qué menciones no cubre
ninguna cita. La cobertura es lo que importa: un informe puede tener las citas perfectas y haberse
salteado la mitad de las menciones.

### 7. Roles y revisión en frío

Un agente que hace todo se corrige a sí mismo. Se divide así:

| Rol | Hace | No hace |
|---|---|---|
| Analista (chat principal) | Mide, arma una ficha por cada parte, decide con vos, verifica cada informe, escribe en la wiki, firma | Pasarte un informe sin verificarlo |
| Redactor | Escribe solo desde la ficha (datos medidos, su base, su fuente, lo que queda afuera) | Medir, decidir ni copiar las frases de la ficha |
| Revisor | Lee en frío y reporta hallazgos con citas verificables | Escribir nada |

- **El revisor arranca de cero cada vez,** idealmente con otro modelo, que tiene otros puntos
  ciegos. Recibe el pedido, el material y los datos, **nunca las conclusiones del analista**. Las
  preguntas abiertas del redactor van en un bloque aparte, que lee recién al terminar.
- **El revisor recibe los datos, no solo el texto.** Una revisión sin datos deja todas las cifras
  sin verificar.
- **Lo que los datos contradicen es gravedad alta,** aunque el argumento siga en pie.
- **El analista clasifica cada hallazgo** como real, aparente (con la razón) o "no alcanza para
  decidir", después de leer su cita en contexto. Los informes crudos se guardan tal como llegaron.
- **Cada punto que un rol le deja a otro se contesta o se pasa,** uno por uno. Una observación que
  nunca le llegó al redactor se repitió tres veces.

### 8. Agentes, workflows y scripts son parte del método, y el método crece

Karpathy dice que el schema evoluciona con el uso. Esto lo convierte en un procedimiento, con tres
tipos de herramienta y reglas para saber cuándo crear cada una. El detalle y las plantillas están
en `template/CLAUDE.md`, sección 8.

**Qué herramienta para qué.**

| Tarea | Herramienta |
|---|---|
| Buscar, contar, comparar entre archivos, controlar que un número siga dando | Script |
| Revisión independiente | Agente nuevo, mejor de otro modelo, con el rol de revisor |
| Una lectura pesada que llenaría la conversación | Agente, modelo fuerte |
| Trabajo repetitivo y verificable que un script no puede hacer | Modelo barato, y solo en ese caso |
| Decidir, diseñar, armar controles, juzgar contradicciones | Chat principal |

Un agente no ahorra uso por correr un modelo más barato. Tiene su propio costo de arranque y lo
que devuelve hay que verificarlo. Se usa por lo que aporta (leer en frío, no llenar la
conversación), no para ahorrar.

**Scripts para tareas repetitivas.** Una tarea es candidata cuando cumple cuatro señales:

- se repite: se hizo dos veces o más y va a volver;
- es mecánica: dos personas la harían igual;
- el resultado se puede comprobar;
- a mano cuesta o se equivoca.

Entonces:

1. El agente **la propone antes de construirla:** qué, cuántas veces apareció, qué haría el script
   y qué no, y cómo se va a saber que funciona.
2. Con tu aprobación, el agente lo construye **de solo lectura** y lo prueba **con errores
   sembrados a propósito**.
3. El agente lo usa **con desconfianza al principio,** contrastando una muestra a mano.

Una tarea que pide criterio nunca se automatiza: un script que decide parece seguro y no lo es.

**Agentes (roles).** Vale la pena crear un rol nuevo cuando un tipo de trabajo vuelve seguido y
pide una postura que el chat principal no puede tener: leer en frío, escribir solo desde datos
medidos, mantener un mapa sin decidir. Un archivo de rol dice:

- quién es y, sobre todo, **qué no hace**;
- qué lee y en qué orden;
- qué escribe;
- qué controla antes de firmar;
- cómo entrega, con bloques de pase para los otros roles;
- con qué modelo corre, y si se conserva durante la sesión o arranca de cero.

Los roles mejoran con **análisis de errores.** Después de una sesión pesada, se leen las
transcripciones de los agentes y se anota cada error con su evidencia y su causa: una regla que
faltaba, una regla ambigua, una regla que no se cumplió o un problema de la herramienta. Después
se corrige el archivo de rol. Los errores más caros suelen estar en lo que el agente *recibió*
(una ficha medida a medias, un pedido incompleto), no en lo que hizo.

**Workflows (guías paso a paso).** Para una tarea que hay que hacer exacta, sobre todo si la hace
una persona a mano en una herramienta que el agente no puede tocar. Cada paso trae **su control
con el valor esperado**, más una tabla de controles final. Un workflow de un solo uso es un
*bloque*: se borra cuando queda ejecutado y verificado, y la página del registro guarda lo que
hizo.

**Cada regla lleva su origen.** Cada regla del schema y de los roles lleva el error que la
originó ("Origin: …"), y el lint marca las que no lo tienen. Cada punto de trabajo cierra con una
pregunta: **¿algo se hizo a mano por segunda vez, o se repitió un error?** Si es así, el agente
propone una regla, un control, un script, un rol o un workflow, y nada se construye sin tu
aprobación.

### 9. Varios que escriben

El esquema de Karpathy es una persona y un agente. Con varios (dos chats, Codex y Claude, un
coautor con el archivo abierto):

- **Un registro de firmas.** Cada escritura agrega una línea a `log.md` con:
  - la hora, **leída del reloj** y nunca estimada;
  - quién escribió, con el modelo, o "no confirmado";
  - los archivos tocados;
  - qué se hizo;
  - qué se controló.
- **Antes de escribir,** el agente lee la cola del log. Si alguien tocó el mismo archivo en los
  últimos ~30 minutos, pregunta primero.
- **El agente lee el archivo en el momento de escribir** y cambia solo su parte. Nunca se rearma
  un archivo desde una copia vieja.
- **Después de guardar, el agente compara byte a byte,** no por tamaño. Un guardado puede dejar la
  versión anterior, y el mismo tamaño no es el mismo contenido.
- **Un archivo que una persona puede tener abierto** (un documento, una planilla) no se escribe
  hasta que confirma que lo cerró. Su próximo guardado pisaría el tuyo.
- Git por debajo, para el historial.

### 10. Un índice con tipos y ciclo de vida

El índice de Karpathy es un catálogo. Acá cada entrada tiene además un **tipo**: estado, página,
método, bloque, referencia, fuente o log. El lint mantiene el índice y la carpeta sincronizados.
Los tipos tienen ciclo de vida:

- un *bloque* (instrucciones de un solo uso) se borra cuando se aplica;
- una *referencia* se lee pero no se mantiene;
- una *fuente* nunca se edita.

### 11. Cuando el proyecto crece

Esta suele ser la primera pregunta sobre el patrón: para un proyecto grande, ¿una wiki o varias?
**Una sola wiki, dividida en áreas,** casi siempre. Partirla en wikis separadas pierde justo lo que
hace valer la pena el patrón: cuando una fuente toca dos áreas se actualizan las dos, y se marcan
las contradicciones entre ellas. Las wikis separadas solo tienen sentido cuando las áreas no tienen
nada que decirse, tienen lectores distintos (una privada, otra compartida) o necesitan schemas que
no encajan entre sí.

**Cuándo dividir:** un archivo de estado que el agente ya no puede leer entero de una vez, un
arranque de sesión que gasta más en leer que en trabajar, un índice que ya no entra en una o dos
pantallas. La división es en sí una decisión, y se hace con un workflow de un solo uso, con el lint
en 0 antes y después.

| Qué crece | Cómo se divide |
|---|---|
| La wiki | Una carpeta por área, `areas/<área>/`, con su propio `index.md` y su `pending.md`. El índice raíz lista `areas/` y nada de adentro. Lo que usan varias áreas va en `shared/`, una página por cosa |
| El schema | Sigue siendo uno. Un área que trabaja distinto tiene un archivo de convenciones solo con lo que cambia |
| El registro | Sigue siendo uno, con numeración global para que los IDs no choquen, y una columna `Area`. Las filas cerradas pasan a `registry-archive.md`, así `registry.md` queda solo con lo abierto |
| El log | Rota por mes: `log/AAAA-MM.md`. Antes de escribir se lee solo la cola del mes en curso |
| Los pendientes | Uno por área. El de la raíz queda solo para lo que bloquea entre áreas |
| Los links | Un nombre de página que existe en dos áreas se enlaza por ruta: `[[areas/sales/overview]]` |

- **Qué se lee al arrancar una sesión:** el índice raíz, el índice y los pendientes del área, las
  filas del registro de esa área y solo las páginas que toca el trabajo.
- **Búsqueda.** Karpathy dice que el índice alcanza hasta unos cientos de páginas y sugiere un
  buscador (qmd) para más. Sirve para *encontrar*. Para *verificar cobertura* (todas las menciones
  de un término, un código o un valor) sigue haciendo falta `wikicheck extract --in <área>`: una
  búsqueda por relevancia no garantiza haber traído todo.
- **Los controles** corren siempre sobre la carpeta entera, porque los links y los valores cruzan
  áreas. `wikicheck lint --only areas/<área>` muestra solo los candidatos de un área mientras se
  trabaja en ella.
- **Revisión:** un revisor por área en paralelo, más uno que solo mira lo que cruza áreas (la misma
  cifra dicha distinto, links entre áreas, un término usado de dos maneras).
- **Una wiki que cita a otra** la declara como cualquier fuente, con su hash, así el lint avisa
  cuando la otra cambia.

`wikicheck` soporta todo esto: controla los sub-índices por carpeta, los logs rotados, el archivo
del registro y la columna `Area`, y `tests/` arma una wiki crecida y le siembra errores. El
procedimiento completo está en `template/CLAUDE.md`, sección 12.

## El ciclo de un punto de trabajo

El ingest, la consulta y el lint de Karpathy pasan a ser un solo ciclo, que sirve para cualquier
unidad de trabajo: una fuente para ingerir, una pregunta, una página, una decisión.

1. **Delimitar** en una línea: qué entra y qué queda afuera. Si crece, se corta.
2. **Leer lo que ya se decidió.** Empezar de cero algo ya resuelto es la forma más cara de perder
   tiempo.
3. **Medir el dato real** antes de proponer nada.
4. **Confrontar las tres versiones:** lo que dice la wiki, lo que hace el sistema y lo que
   muestran los datos. Si no coinciden, *ese* es el trabajo.
5. **Decidir lo que falte,** numerado y con su porqué. Si la decisión es tuya, el agente trae las
   opciones con lo que se gana y lo que se pierde, medido.
6. **Ejecutar y validar,** con controles que fallan fuerte. Un cambio sin control no está
   terminado.
7. **Registrar:** la fila, su página con el porqué, `pending.md` y el log, todo en el mismo
   movimiento.
8. **Cerrar:** qué quedó resuelto, qué quedó abierto, de quién depende, y la pregunta de la
   repetición (8).

## Costos

- **Carga de trabajo.** El protocolo completo se justifica cuando la wiki respalda números que
  alguien tiene que defender, o cuando la comparten varios que escriben. Para notas personales, la
  versión liviana de Karpathy probablemente alcanza. Todo esto es modular.
- **Otro énfasis.** Esto hace la wiki más confiable y más segura de cambiar. No mejora la síntesis
  en sí: eso sigue dependiendo del modelo y de tus preguntas.

## Qué hay en este repo

```
template/          una carpeta para arrancar: copiala para empezar
  CLAUDE.md        el schema (renombralo a AGENTS.md para Codex)
  index.md         una línea por archivo, con su tipo
  registry.md      solo tablas: D, H, T, P y valores reemplazados
  registry/        una página por ID
  pending.md       lo que falta hacer
  log.md           el registro de firmas
  roles/           redactor, revisor y una plantilla para roles nuevos
  workflows/       una plantilla para guías paso a paso con controles
  wiki/ raw/ snapshots/ reviews/
tools/wikicheck.py el verificador de solo lectura (solo biblioteca estándar, Python 3.9+)
example/           una wiki mínima (métricas de pedidos de una tienda online) que pasa todos los controles
tests/             cada control probado contra errores sembrados, también en una wiki crecida con áreas
```

```
python tools/wikicheck.py lint     --root mi-wiki
python tools/wikicheck.py lint     --root mi-wiki --only areas/sales   # los candidatos de un área
python tools/wikicheck.py snapshot --root mi-wiki                  # compara raw/ con la última foto
python tools/wikicheck.py snapshot --root mi-wiki --out "snapshots/2026-10-28 1415.json"
python tools/wikicheck.py cite informe.md --root mi-wiki --files wiki/metrics.md --terms shipping
python tools/wikicheck.py hash     mi-wiki/raw/orders.csv          # para el frontmatter sources: de una página
python tools/wikicheck.py extract  refund --root mi-wiki           # cada mención, con su párrafo o su fila de tabla
python tools/wikicheck.py extract  refund --root mi-wiki --in areas/sales
```

**Para arrancar:**

1. Copiá `template/` a una carpeta nueva.
2. Dale este README y `CLAUDE.md` a tu agente, y completen juntos la sección 1 de `CLAUDE.md`.
3. Corré `wikicheck lint` y `wikicheck snapshot` al arrancar cada sesión.

La plantilla y el ejemplo están en inglés. Para ver cada control fallar a propósito, mirá `tests/`.

## Créditos

El patrón LLM Wiki es de Andrej Karpathy
([gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)). Este repo lo extiende
y no está afiliado a él. Licencia MIT.
