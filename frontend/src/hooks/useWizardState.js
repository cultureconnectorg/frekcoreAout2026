import { useReducer, useCallback } from 'react';

const initialState = {
  currentStep: 1,
  // Step 1 - Identity
  artist: {
    name: '',
    legal_name: '',
    territory: 'MQ',
  },
  event: {
    name: '',
    date: new Date().toISOString().split('T')[0],
    start_time: '',
    venue: '',
    city: '',
    context: 'live',
  },
  // Step 2 - Tracklist
  tracklist: [],
  // Step 3 - Fingerprint
  audioFile: null,
  audioFingerprint: {
    method: '',
    value: '',
    algorithm: '',
    sample_rate: 44100,
    fft_size: 2048,
    duration: 0,
  },
  // Step 4 - Generated
  mixId: '',
  createdAt: '',
  signature: {
    method: 'sha256-self',
    value: '',
  },
  // UI State
  isGenerating: false,
  isComplete: false,
  errors: {},
};

function wizardReducer(state, action) {
  switch (action.type) {
    case 'SET_STEP':
      return { ...state, currentStep: action.payload };
    case 'NEXT_STEP':
      return { ...state, currentStep: Math.min(state.currentStep + 1, 4) };
    case 'PREV_STEP':
      return { ...state, currentStep: Math.max(state.currentStep - 1, 1) };
    case 'UPDATE_ARTIST':
      return { ...state, artist: { ...state.artist, ...action.payload } };
    case 'UPDATE_EVENT':
      return { ...state, event: { ...state.event, ...action.payload } };
    case 'SET_TRACKLIST':
      return { ...state, tracklist: action.payload };
    case 'ADD_TRACK':
      return {
        ...state,
        tracklist: [
          ...state.tracklist,
          {
            position: state.tracklist.length + 1,
            title: '',
            artist: '',
            isrc: '',
            start_time: '',
          },
        ],
      };
    case 'UPDATE_TRACK':
      return {
        ...state,
        tracklist: state.tracklist.map((track, i) =>
          i === action.payload.index
            ? { ...track, ...action.payload.data }
            : track
        ),
      };
    case 'REMOVE_TRACK':
      return {
        ...state,
        tracklist: state.tracklist
          .filter((_, i) => i !== action.payload)
          .map((track, i) => ({ ...track, position: i + 1 })),
      };
    case 'MOVE_TRACK_UP':
      if (action.payload === 0) return state;
      const upList = [...state.tracklist];
      [upList[action.payload - 1], upList[action.payload]] = [
        upList[action.payload],
        upList[action.payload - 1],
      ];
      return {
        ...state,
        tracklist: upList.map((t, i) => ({ ...t, position: i + 1 })),
      };
    case 'MOVE_TRACK_DOWN':
      if (action.payload === state.tracklist.length - 1) return state;
      const downList = [...state.tracklist];
      [downList[action.payload], downList[action.payload + 1]] = [
        downList[action.payload + 1],
        downList[action.payload],
      ];
      return {
        ...state,
        tracklist: downList.map((t, i) => ({ ...t, position: i + 1 })),
      };
    case 'SET_AUDIO_FILE':
      return { ...state, audioFile: action.payload };
    case 'SET_FINGERPRINT':
      return { ...state, audioFingerprint: { ...state.audioFingerprint, ...action.payload } };
    case 'SET_MIX_ID':
      return { ...state, mixId: action.payload };
    case 'SET_CREATED_AT':
      return { ...state, createdAt: action.payload };
    case 'SET_SIGNATURE':
      return { ...state, signature: { ...state.signature, ...action.payload } };
    case 'SET_GENERATING':
      return { ...state, isGenerating: action.payload };
    case 'SET_COMPLETE':
      return { ...state, isComplete: action.payload };
    case 'SET_ERRORS':
      return { ...state, errors: action.payload };
    case 'RESET':
      return initialState;
    default:
      return state;
  }
}

export function useWizardState() {
  const [state, dispatch] = useReducer(wizardReducer, initialState);

  const setStep = useCallback((step) => {
    dispatch({ type: 'SET_STEP', payload: step });
  }, []);

  const nextStep = useCallback(() => {
    dispatch({ type: 'NEXT_STEP' });
  }, []);

  const prevStep = useCallback(() => {
    dispatch({ type: 'PREV_STEP' });
  }, []);

  const updateArtist = useCallback((data) => {
    dispatch({ type: 'UPDATE_ARTIST', payload: data });
  }, []);

  const updateEvent = useCallback((data) => {
    dispatch({ type: 'UPDATE_EVENT', payload: data });
  }, []);

  const addTrack = useCallback(() => {
    dispatch({ type: 'ADD_TRACK' });
  }, []);

  const updateTrack = useCallback((index, data) => {
    dispatch({ type: 'UPDATE_TRACK', payload: { index, data } });
  }, []);

  const removeTrack = useCallback((index) => {
    dispatch({ type: 'REMOVE_TRACK', payload: index });
  }, []);

  const moveTrackUp = useCallback((index) => {
    dispatch({ type: 'MOVE_TRACK_UP', payload: index });
  }, []);

  const moveTrackDown = useCallback((index) => {
    dispatch({ type: 'MOVE_TRACK_DOWN', payload: index });
  }, []);

  const setAudioFile = useCallback((file) => {
    dispatch({ type: 'SET_AUDIO_FILE', payload: file });
  }, []);

  const setFingerprint = useCallback((data) => {
    dispatch({ type: 'SET_FINGERPRINT', payload: data });
  }, []);

  const setMixId = useCallback((id) => {
    dispatch({ type: 'SET_MIX_ID', payload: id });
  }, []);

  const setCreatedAt = useCallback((timestamp) => {
    dispatch({ type: 'SET_CREATED_AT', payload: timestamp });
  }, []);

  const setSignature = useCallback((data) => {
    dispatch({ type: 'SET_SIGNATURE', payload: data });
  }, []);

  const setGenerating = useCallback((value) => {
    dispatch({ type: 'SET_GENERATING', payload: value });
  }, []);

  const setComplete = useCallback((value) => {
    dispatch({ type: 'SET_COMPLETE', payload: value });
  }, []);

  const setErrors = useCallback((errors) => {
    dispatch({ type: 'SET_ERRORS', payload: errors });
  }, []);

  const reset = useCallback(() => {
    dispatch({ type: 'RESET' });
  }, []);

  return {
    state,
    setStep,
    nextStep,
    prevStep,
    updateArtist,
    updateEvent,
    addTrack,
    updateTrack,
    removeTrack,
    moveTrackUp,
    moveTrackDown,
    setAudioFile,
    setFingerprint,
    setMixId,
    setCreatedAt,
    setSignature,
    setGenerating,
    setComplete,
    setErrors,
    reset,
  };
}

export default useWizardState;
