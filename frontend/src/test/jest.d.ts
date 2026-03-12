declare const vi: {
  mock: (moduleName: string, factory: any) => void;
  fn: (implementation?: any) => any;
  spOn: (object: any, method: string) => any;
  clearAllMocks: () => void;
  resetAllMocks: () => void;
  restoreAllMocks: () => void;
  deepMock: (moduleName: string, factory: any) => void;
};

declare global {
  const jest: typeof vi & {
    clearAllMocks: () => void;
    resetAllMocks: () => void;
    restoreAllMocks: () => void;
    doMock: (moduleName: string, factory?: any) => void;
    requireActual: (moduleName: string) => any;
  };
}

export {};
