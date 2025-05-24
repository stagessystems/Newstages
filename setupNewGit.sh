#!/bin/bash

# Script to add a new Git remote origin and verify it
NEW_ORIGIN="https://github.com/stagessystems/Newstages.git"
REMOTE_NAME="company"  # Change to another name (e.g., "upstream") if you want to keep the old origin

# Check if current directory is a Git repo
if [ ! -d .git ] && ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "Error: This is not a Git repository. Run this script from the root of your repo."
  exit 1
fi

# Check if remote already exists
EXISTING_URL=$(git remote get-url "$REMOTE_NAME" 2> /dev/null)

if [ -n "$EXISTING_URL" ]; then
  echo "Warning: Remote '$REMOTE_NAME' already points to: $EXISTING_URL"
  read -p "Do you want to overwrite it? (y/N) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted. No changes made."
    exit 0
  fi
fi

# Set new origin
git remote set-url "$REMOTE_NAME" "$NEW_ORIGIN" || git remote add "$REMOTE_NAME" "$NEW_ORIGIN"

# Verify
echo "New remote URL set:"
git remote -v | grep "$REMOTE_NAME"

# Optional: Push to new origin
read -p "Do you want to push to the new origin now? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  CURRENT_BRANCH=$(git branch --show-current)
  echo "Pushing '$CURRENT_BRANCH' to '$REMOTE_NAME'..."
  git push -u "$REMOTE_NAME" "$CURRENT_BRANCH"
fi

echo "Done!"

