declare module "next/dynamic" {
  export default function dynamic(loader: () => Promise<unknown>): unknown;
}
