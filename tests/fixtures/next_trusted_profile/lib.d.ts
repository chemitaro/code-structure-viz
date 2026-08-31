export declare interface Array<T> {
  map<U>(callback: (value: T) => U): U[];
  flatMap<U>(callback: (value: T) => U | U[]): U[];
}
export declare interface ReadonlyArray<T> {
  map<U>(callback: (value: T) => U): U[];
  flatMap<U>(callback: (value: T) => U | U[]): U[];
}
export declare interface JSX {
  interface Element {}
}
