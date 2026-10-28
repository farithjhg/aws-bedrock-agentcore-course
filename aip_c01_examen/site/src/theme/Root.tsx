import React from 'react';
import type {ReactNode} from 'react';
import BrowserOnly from '@docusaurus/BrowserOnly';
import ChatWidget from '../components/ChatWidget';

export default function Root({children}: {children: ReactNode}) {
  return (
    <>
      {children}
      <BrowserOnly>{() => <ChatWidget />}</BrowserOnly>
    </>
  );
}
