import { AppProps } from "next/app";
import Head from "next/head";
import { MantineProvider } from "@mantine/core";
import { useColorScheme } from '@mantine/hooks';

export default function App(props: AppProps) {
  const { Component, pageProps } = props;
  const colorScheme = useColorScheme();

  return (
    <>
      <Head>
        <title>Course Calendar Link Generation</title>
        <link rel="shortcut icon" href="/favicon.svg" />
        <meta
          name="viewport"
          content="minimum-scale=1, initial-scale=1, width=device-width"
        />
      </Head>

      <MantineProvider
        withGlobalStyles
        withNormalizeCSS
        theme={{
          /** Put your mantine theme override here */
          colorScheme: colorScheme,
        }}
      >
        <Component {...pageProps} />
      </MantineProvider>
    </>
  );
}
