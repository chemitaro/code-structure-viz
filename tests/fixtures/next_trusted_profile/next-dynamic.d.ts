declare module "next/dynamic" {
  export default function dynamic(loader: () => unknown): unknown;
}
