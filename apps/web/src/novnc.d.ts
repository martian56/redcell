// @novnc/novnc ships no type declarations; declare the slice of RFB we use.
declare module '@novnc/novnc' {
  export interface RFBOptions {
    shared?: boolean;
    credentials?: { password?: string };
  }
  export default class RFB {
    constructor(target: Element, url: string, options?: RFBOptions);
    viewOnly: boolean;
    scaleViewport: boolean;
    addEventListener(type: string, listener: (e: Event) => void): void;
    removeEventListener(type: string, listener: (e: Event) => void): void;
    disconnect(): void;
  }
}
