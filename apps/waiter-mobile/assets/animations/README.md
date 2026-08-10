# Animações Rive

Assets de exemplo oficiais do runtime Rive para Flutter (MIT), usados como
ponto de partida genérico enquanto não temos arte com a marca do restaurante:

- `liquid_download.riv` — indicador de carregamento (tela de loading/splash).
- `rewards.riv` — animação de recompensa/sucesso com data-binding (moedas),
  usada como celebração ao concluir uma ação (ex: pedido enviado com sucesso).

Fonte: https://github.com/rive-app/rive-flutter/tree/master/example/assets
(licença MIT do runtime; arquivos de demonstração do próprio time do Rive,
usados nos tutoriais oficiais — ver `docs/runtimes/data-binding` em rive.app).

Para trocar por animações com a identidade visual do restaurante: crie os
arquivos no editor (https://rive.app/editor) e substitua os `.riv` acima
pelo mesmo nome de arquivo — nenhum código muda se as ViewModels/nomes de
propriedade forem mantidos (ver `lib/presentation/widgets/rive/`).
