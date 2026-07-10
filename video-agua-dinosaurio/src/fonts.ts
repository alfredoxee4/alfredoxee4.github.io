import { continueRender, delayRender, staticFile } from "remotion";

let started = false;

const loadOne = async (
  family: string,
  file: string,
  descriptors?: FontFaceDescriptors
): Promise<void> => {
  const res = await fetch(staticFile(file));
  const buf = await res.arrayBuffer();
  const face = new FontFace(family, buf, descriptors);
  await face.load();
  document.fonts.add(face);
};

export const loadFonts = (): void => {
  if (started || typeof document === "undefined") {
    return;
  }
  started = true;
  const handle = delayRender("fonts", {
    retries: 2,
    timeoutInMilliseconds: 60000,
  });
  Promise.all([
    loadOne("Archivo Black", "fonts/ArchivoBlack-Regular.ttf"),
    loadOne("Montserrat", "fonts/Montserrat-Variable.ttf", {
      weight: "100 900",
    }),
  ])
    .then(() => continueRender(handle))
    .catch((err) => {
      // eslint-disable-next-line no-console
      console.error("Error cargando fuentes", err);
      continueRender(handle);
    });
};
