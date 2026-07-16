import childProcess from "node:child_process";
import { syncBuiltinESMExports } from "node:module";

const originalExec = childProcess.exec;

childProcess.exec = (command, ...args) => {
  if (command === "net use") {
    const callback = args.find((argument) => typeof argument === "function");
    queueMicrotask(() => callback?.(null, "", ""));
    return undefined;
  }

  return originalExec(command, ...args);
};

syncBuiltinESMExports();
await import("../node_modules/vite/bin/vite.js");
