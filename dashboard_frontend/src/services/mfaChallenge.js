let pendingCredentials = null;

export const setMfaPendingCredentials = ({ username, password }) => {
  pendingCredentials = { username, password };
};

export const getMfaPendingCredentials = () => pendingCredentials;

export const clearMfaPendingCredentials = () => {
  pendingCredentials = null;
};
