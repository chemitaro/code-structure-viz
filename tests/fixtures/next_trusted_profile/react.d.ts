declare module "react" {
  export class Component<P = unknown> {}
  export function createElement(type: unknown, props: unknown): unknown;
  export function forwardRef(render: unknown): unknown;
  export function lazy(loader: () => unknown): unknown;
  export function memo(component: unknown): unknown;
}
