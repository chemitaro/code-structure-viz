interface Array<T> {
  map<U>(callback: (value: T) => U): U[];
  flatMap<U>(callback: (value: T) => U | U[]): U[];
}
interface ReadonlyArray<T> {
  map<U>(callback: (value: T) => U): U[];
  flatMap<U>(callback: (value: T) => U | U[]): U[];
}
declare namespace JSX {
  interface Element {}
}
