import React from 'react';
// `Rive` (o componente React) é o export default do pacote — `@rive-app/react-canvas`
// também re-exporta tudo de `@rive-app/canvas`, que tem uma classe *nomeada*
// `Rive` (a API imperativa, não-React); um import nomeado pegaria a errada.
import RiveComponent, { Fit, Layout } from '@rive-app/react-canvas';

const CONTAIN_LAYOUT = new Layout({ fit: Fit.Contain });

interface RiveLoadingIndicatorProps {
  size?: number;
  className?: string;
}

/**
 * Indicador de carregamento animado (Rive) — mesmo asset usado nos apps
 * Flutter (`assets/animations/liquid_download.riv`, ver
 * `public/animations/README.md` pra fonte/licença).
 */
export const RiveLoadingIndicator: React.FC<RiveLoadingIndicatorProps> = ({
  size = 96,
  className = '',
}) => (
  <div style={{ width: size, height: size }} className={className}>
    <RiveComponent src="/animations/liquid_download.riv" layout={CONTAIN_LAYOUT} />
  </div>
);
