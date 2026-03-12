import { AppProvider } from './hooks/useAppState';
import Layout from './components/Layout';

function App() {
  return (
    <AppProvider>
      <Layout />
    </AppProvider>
  );
}

export default App;
